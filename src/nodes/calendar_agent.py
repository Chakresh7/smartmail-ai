"""Calendar agent node

Detects calendar events in an email and optionally creates them
via the `CalendarClient` wrapper when enabled.
"""

from typing import List
from config.config import settings
from src.utils.prompts import build_calendar_extraction_prompt
from src.utils.schemas import EmailData, CalendarEventData
from src.tools.calendar_tools import CalendarClient
from src.utils.helpers import safe_json_parse, setup_logging

try:
	from openai import OpenAI
except Exception:
	OpenAI = None

logger = setup_logging(log_level=settings.log_level)


def detect_calendar_events(email: EmailData) -> List[CalendarEventData]:
	prompt = build_calendar_extraction_prompt(email.subject or "", email.body or "", timezone="UTC")

	if settings.dry_run_mode or OpenAI is None or not settings.openai_api_key:
		return []

	try:
		client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base_url)
		resp = client.responses.create(model=settings.llm_model, input=prompt, max_tokens=300)
		text = str(resp)
		parsed = safe_json_parse(text, default=None)
		events = []
		if parsed and isinstance(parsed, dict):
			for ev in parsed.get("events", []):
				try:
					events.append(
						CalendarEventData(
							title=ev.get("title", "Meeting"),
							description=ev.get("description", ""),
							start_time=ev.get("start_time"),
							end_time=ev.get("end_time"),
							attendees=ev.get("attendees", []),
							location=ev.get("location"),
							timezone=ev.get("timezone", "UTC"),
							source_email_id=email.email_id,
							confidence=float(ev.get("confidence", 0.0)),
							requires_confirmation=True,
						)
					)
				except Exception:
					continue

		# Optionally create events
		created = []
		if settings.enable_auto_calendar_creation and events:
			cal = CalendarClient()
			for ev in events:
				try:
					if ev.confidence >= settings.calendar_detection_confidence:
						cal.create_event(ev)
						created.append(ev)
				except Exception as exc:
					logger.warning(f"Failed to create calendar event: {exc}")

		return events
	except Exception as exc:
		logger.warning(f"Calendar extraction failed: {exc}")
		return []

