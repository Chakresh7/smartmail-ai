"""Utilities package for SmartMail AI."""

from .schemas import (
    EmailData,
    ClassificationResult,
    SummaryResult,
    ReplyDraft,
    CalendarEventData,
    GraphState,
    EmailType,
    EmailPriority,
    EmailIntent,
)
from .helpers import (
    setup_logging,
    count_tokens,
    clean_email_text,
    extract_email_addresses,
    truncate_text,
    safe_json_parse,
    SmartMailException,
    retry_with_backoff,
)
from .prompts import (
    build_classification_prompt,
    build_summarization_prompt,
    build_reply_prompt,
    build_calendar_extraction_prompt,
)

__all__ = [
    # Schemas
    "EmailData",
    "ClassificationResult",
    "SummaryResult",
    "ReplyDraft",
    "CalendarEventData",
    "GraphState",
    "EmailType",
    "EmailPriority",
    "EmailIntent",
    # Helpers
    "setup_logging",
    "count_tokens",
    "clean_email_text",
    "extract_email_addresses",
    "truncate_text",
    "safe_json_parse",
    "SmartMailException",
    "retry_with_backoff",
    # Prompts
    "build_classification_prompt",
    "build_summarization_prompt",
    "build_reply_prompt",
    "build_calendar_extraction_prompt",
]
