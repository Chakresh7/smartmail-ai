"""Email classification node

Provides a lightweight classifier node that builds a classification
prompt and attempts to call the configured LLM provider. Falls back
to a deterministic heuristic when LLM calls fail or when running in
dry-run mode.
"""

from typing import Optional
import json

from config.config import settings
from src.utils.prompts import build_classification_prompt
from src.utils.schemas import EmailData, ClassificationResult, EmailType, EmailPriority, EmailIntent
from src.utils.helpers import safe_json_parse, setup_logging, extract_text_from_response

try:
	from openai import OpenAI
except Exception:
	OpenAI = None

logger = setup_logging(log_level=settings.log_level)


def classify_email(email: EmailData) -> ClassificationResult:
	"""Classify an email and return a `ClassificationResult`.

	Uses the project's prompt templates and the configured LLM provider.
	If `settings.dry_run_mode` is True or the LLM call fails, returns
	a heuristic-based classification.
	"""
	prompt = build_classification_prompt(email.subject or "", email.body or "")

	# Dry-run / fallback heuristic
	if settings.dry_run_mode or OpenAI is None or not settings.openai_api_key:
		# Simple heuristic
		lower = (email.subject + " " + email.body).lower()
		if "meeting" in lower or "schedule" in lower:
			etype = EmailType.MEETING_REQUEST
		elif "urgent" in lower or "asap" in lower:
			etype = EmailType.URGENT
		else:
			etype = EmailType.GENERAL_EMAIL

		result = ClassificationResult(
			email_id=email.email_id,
			email_type=etype,
			priority=EmailPriority.NORMAL,
			intent=EmailIntent.INFORMATIONAL,
			type_confidence=0.6,
			priority_confidence=0.6,
			intent_confidence=0.6,
			reasoning="Heuristic fallback classification",
			requires_human_review=False,
			category_tags=[],
		)
		return result

	# Attempt real LLM call
	try:
		client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base_url)
		resp = client.responses.create(model=settings.llm_model, input=prompt, max_tokens=400)
		text = extract_text_from_response(resp)
		parsed = safe_json_parse(text, default=None)
		if parsed:
			# Map parsed JSON to ClassificationResult
			return ClassificationResult(
				email_id=email.email_id,
				email_type=EmailType(parsed.get("email_type", "general_email")),
				priority=EmailPriority(parsed.get("priority", "normal")),
				intent=EmailIntent(parsed.get("intent", "informational")),
				type_confidence=float(parsed.get("type_confidence", 0.0)),
				priority_confidence=float(parsed.get("priority_confidence", 0.0)),
				intent_confidence=float(parsed.get("intent_confidence", 0.0)),
				reasoning=parsed.get("reasoning", ""),
				requires_human_review=parsed.get("requires_human_review", False),
				category_tags=parsed.get("category_tags", []),
			)
	except Exception as exc:
		logger.warning(f"LLM classification failed, falling back: {exc}")

	# Final fallback
	return ClassificationResult(
		email_id=email.email_id,
		email_type=EmailType.GENERAL_EMAIL,
		priority=EmailPriority.NORMAL,
		intent=EmailIntent.INFORMATIONAL,
		type_confidence=0.5,
		priority_confidence=0.5,
		intent_confidence=0.5,
		reasoning="Fallback after LLM error",
		requires_human_review=False,
		category_tags=[],
	)

