"""Simple orchestration runner for SmartMail AI (Phase 4).

This runner executes a linear processing pipeline over unread emails:
1. Fetch unread
2. Classify
3. Retrieve RAG context
4. Summarize & extract actions
5. Generate reply draft
6. Detect calendar events
7. Decide human review / save draft

This is a minimal runner intended for local development and testing
before integrating a full LangGraph or LangChain orchestration layer.
"""

from src.nodes import (
	fetch_unread_emails,
	classify_email,
	retrieve_context,
	summarize_and_extract,
	generate_reply_draft,
	detect_calendar_events,
	create_human_review_item,
)
from src.tools.gmail_tools import GmailClient
from src.utils.helpers import setup_logging
from config.config import settings
from src.utils.schemas import GraphState


logger = setup_logging(log_level=settings.log_level)


def process_email(email):
	state = GraphState()
	state.email = email
	state.email_id = email.email_id

	# 1. classify
	state.classification = classify_email(email)

	# 2. RAG retrieval
	state.rag_context = retrieve_context(email)

	# 3. Summarize + actions
	state.summary = summarize_and_extract(email, state.rag_context)

	# 4. Reply generation
	state.reply_draft = generate_reply_draft(email, state.rag_context)

	# 5. Calendar events
	state.calendar_events = detect_calendar_events(email)

	# 6. Human review decision
	needs_review = False
	if state.classification and state.classification.type_confidence < settings.classification_confidence_threshold:
		needs_review = True

	if state.reply_draft and state.reply_draft.confidence < settings.reply_confidence_threshold:
		needs_review = True

	state.requires_human_review = needs_review

	if needs_review and settings.enable_human_review:
		create_human_review_item(state, reason="Low confidence in automated pipeline")
	else:
		# Save draft if available
		try:
			if state.reply_draft and settings.enable_auto_reply_drafting:
				gmail = GmailClient()
				gmail.save_draft(state.email.email_id, state.reply_draft.reply_text)
		except Exception as exc:
			logger.warning(f"Failed to save draft: {exc}")

	return state


def run_once(max_messages: int = 5):
	emails = fetch_unread_emails(max_results=max_messages)
	results = []
	for e in emails:
		logger.info(f"Processing email {e.email_id} - {e.subject}")
		r = process_email(e)
		results.append(r)
	return results


if __name__ == "__main__":
	run_once(max_messages=5)

