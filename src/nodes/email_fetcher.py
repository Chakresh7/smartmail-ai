"""Email fetcher node

Provides a small node that fetches unread emails from Gmail and
parses them into `EmailData` models.
"""

from typing import List, Optional

from config.config import settings
from src.tools.gmail_tools import GmailClient
from src.utils.schemas import EmailData
from src.utils.helpers import setup_logging

logger = setup_logging(log_level=settings.log_level)


def fetch_unread_emails(max_results: Optional[int] = None, label_ids: Optional[List[str]] = None) -> List[EmailData]:
	"""Fetch unread emails using the Gmail wrapper and return parsed `EmailData` objects.

	Args:
		max_results: maximum number of messages to fetch (overrides settings.gmail_batch_size)
		label_ids: optional Gmail label filter

	Returns:
		List[EmailData]
	"""
	client = GmailClient(credentials_path=settings.gmail_credentials_path)
	try:
		limit = max_results or settings.gmail_batch_size
		messages = client.fetch_unread_messages(max_results=limit, label_ids=label_ids)
		emails = []
		for msg in messages:
			msg_id = msg.get("id")
			try:
				raw = client.get_message(msg_id)
				email = client.parse_message(raw)
				emails.append(email)
			except Exception as exc:
				logger.warning(f"Failed to fetch/parse message {msg_id}: {exc}")
		return emails
	except Exception as exc:
		logger.error(f"Error fetching unread emails: {exc}")
		return []

