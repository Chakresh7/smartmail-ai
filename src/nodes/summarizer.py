"""Summarization and action extraction node

Uses prompt templates to produce a concise summary and extract action items.
Falls back to simple heuristics when LLM calls are not available or fail.
"""

from typing import List, Optional
from config.config import settings
from src.utils.prompts import build_summarization_prompt, build_action_extraction_prompt
from src.utils.schemas import EmailData, SummaryResult, ActionItem
from src.utils.helpers import safe_json_parse, setup_logging, extract_text_from_response

try:
	from openai import OpenAI
except Exception:
	OpenAI = None

logger = setup_logging(log_level=settings.log_level)


def summarize_and_extract(email: EmailData, rag_context: Optional[List[dict]] = None) -> SummaryResult:
	prompt = build_summarization_prompt(email.subject or "", email.body or "")
	action_prompt = build_action_extraction_prompt(email.subject or "", email.body or "")

	# Default fallback
	default_summary = SummaryResult(
		email_id=email.email_id,
		summary=(email.body[:200] + "...") if len(email.body) > 200 else email.body,
		key_points=[],
		action_items=[],
		sentiment="neutral",
		entities={},
	)

	if settings.dry_run_mode or OpenAI is None or not settings.openai_api_key:
		return default_summary

	try:
		client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base_url)
		request_kwargs = {
			"model": settings.llm_model,
			"input": prompt,
			"temperature": settings.llm_temperature,
		}
		if settings.llm_max_tokens:
			request_kwargs["max_output_tokens"] = settings.llm_max_tokens
		resp = client.responses.create(**request_kwargs)
		text = extract_text_from_response(resp)
		parsed = safe_json_parse(text, default=None)
		if parsed:
			# Build ActionItem models from parsed action items if present
			actions = []
			for a in parsed.get("action_items", []):
				actions.append(
					ActionItem(
						action=a.get("action", ""),
						assigned_to=a.get("assigned_to"),
						due_date=None,
						priority=a.get("priority", "normal"),
						status="pending",
					)
				)

			return SummaryResult(
				email_id=email.email_id,
				summary=parsed.get("summary", default_summary.summary),
				key_points=parsed.get("key_points", []),
				action_items=actions,
				sentiment=parsed.get("sentiment", "neutral"),
				entities=parsed.get("entities", {}),
			)
	except Exception as exc:
		logger.warning(f"Summarization LLM call failed: {exc}")

	return default_summary

