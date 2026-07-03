"""Reply generation node

Generates a reply draft using the reply prompt and optional RAG context.
"""

from typing import List, Optional
from config.config import settings
from src.utils.prompts import build_reply_prompt
from src.utils.schemas import EmailData, ReplyDraft, RAGContext
from src.utils.helpers import setup_logging, safe_json_parse, extract_text_from_response

try:
	from openai import OpenAI
except Exception:
	OpenAI = None

logger = setup_logging(log_level=settings.log_level)


def generate_reply_draft(email: EmailData, rag_contexts: Optional[List[RAGContext]] = None) -> ReplyDraft:
	rag_text = "\n".join([c.snippet for c in (rag_contexts or [])])
	prompt = build_reply_prompt(email.subject or "", email.sender or "", email.body or "", rag_context=rag_text)

	# Default fallback draft
	default = ReplyDraft(
		email_id=email.email_id,
		reply_text=f"Thanks for your message regarding {email.subject}. I'll follow up shortly.",
		tone="professional",
		confidence=0.5,
		requires_editing=True,
		suggestions=[],
	)

	if settings.dry_run_mode or OpenAI is None or not settings.openai_api_key:
		return default

	try:
		client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base_url)
		resp = client.responses.create(model=settings.llm_model, input=prompt, max_tokens=500)
		text = extract_text_from_response(resp)
		# Best-effort parse plain text reply
		reply_text = None
		parsed = safe_json_parse(text, default=None)
		if parsed and isinstance(parsed, str):
			reply_text = parsed
		else:
			# fallback: try to extract any text content
			reply_text = text

		return ReplyDraft(
			email_id=email.email_id,
			reply_text=reply_text,
			tone="professional",
			confidence=0.8,
			requires_editing=False,
			suggestions=[],
		)
	except Exception as exc:
		logger.warning(f"Reply generation failed: {exc}")
		return default

