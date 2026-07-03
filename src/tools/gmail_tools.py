"""
Gmail API wrapper for SmartMail AI.

This module provides a small abstraction over Gmail API operations,
including authentication, fetching emails, and saving drafts.
"""

from __future__ import annotations

import base64
from email.message import EmailMessage
from datetime import datetime
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.config import settings
from src.utils.schemas import EmailData
from src.utils.helpers import clean_email_text, SmartMailException


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailAPIError(SmartMailException):
    """Raised when the Gmail API client encounters an error."""
    pass


class GmailClient:
    """Client for Gmail API operations."""

    def __init__(self, credentials_path: str = settings.gmail_credentials_path):
        self.credentials_path = credentials_path
        self.creds: Optional[Credentials] = None
        self.service = self._authorize()

    def _authorize(self) -> Any:
        """Authorize and return a Gmail API service object."""
        creds = None
        try:
            creds = Credentials.from_authorized_user_file(self.credentials_path, SCOPES)
        except Exception:
            pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.credentials_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        self.creds = creds
        return build("gmail", "v1", credentials=creds)

    def fetch_unread_messages(self, max_results: int = 10, label_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch unread Gmail messages with optional label filtering."""
        try:
            request = self.service.users().messages().list(
                userId="me",
                q="is:unread",
                labelIds=label_ids,
                maxResults=max_results,
            )
            response = request.execute()
            return response.get("messages", [])
        except Exception as exc:
            raise GmailAPIError(f"Error fetching unread messages: {exc}") from exc

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Retrieve a single Gmail message by ID."""
        try:
            result = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute()
            return result
        except Exception as exc:
            raise GmailAPIError(f"Error retrieving message {message_id}: {exc}") from exc

    def parse_message(self, raw_message: Dict[str, Any]) -> EmailData:
        """Parse raw Gmail message data into EmailData."""
        try:
            headers = {item["name"]: item["value"] for item in raw_message.get("payload", {}).get("headers", [])}

            subject = headers.get("Subject", "")
            sender = headers.get("From", "")
            to_header = headers.get("To", "")
            cc_header = headers.get("Cc", "")
            thread_id = raw_message.get("threadId", "")
            email_id = raw_message.get("id", "")
            received_at = self._parse_internal_date(raw_message.get("internalDate"))
            body, html_body = self._extract_body(raw_message.get("payload", {}))
            attachments = self._extract_attachment_filenames(raw_message.get("payload", {}))

            return EmailData(
                email_id=email_id,
                thread_id=thread_id,
                subject=subject,
                sender=sender,
                sender_name=self._extract_sender_name(sender),
                to=self._split_addresses(to_header),
                cc=self._split_addresses(cc_header),
                bcc=[],
                body=clean_email_text(body or html_body or ""),
                html_body=html_body,
                received_at=received_at,
                is_reply="In-Reply-To" in headers,
                labels=raw_message.get("labelIds", []),
                attachments=attachments,
            )
        except Exception as exc:
            raise GmailAPIError(f"Error parsing Gmail message: {exc}") from exc

    def save_draft(self, email_id: str, draft_text: str) -> Dict[str, Any]:
        """Save a draft reply to Gmail for the provided email."""
        try:
            original = self.get_message(email_id)
            headers = {item["name"]: item["value"] for item in original.get("payload", {}).get("headers", [])}
            reply_to = headers.get("From", "")
            subject = headers.get("Subject", "")

            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"

            thread_id = original.get("threadId")
            message = self._build_draft_message(reply_to, subject, draft_text, thread_id=thread_id)

            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": message},
            ).execute()
            return draft
        except Exception as exc:
            raise GmailAPIError(f"Error saving draft for message {email_id}: {exc}") from exc

    def mark_as_read(self, message_id: str) -> None:
        """Mark a Gmail message as read."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
        except Exception as exc:
            raise GmailAPIError(f"Error marking message {message_id} as read: {exc}") from exc

    @staticmethod
    def _extract_body(payload: Dict[str, Any]) -> tuple[str, Optional[str]]:
        if payload.get("mimeType") == "text/plain":
            return GmailClient._decode_base64(payload.get("body", {}).get("data", "")), None
        if payload.get("mimeType") == "text/html":
            return "", GmailClient._decode_base64(payload.get("body", {}).get("data", ""))

        for part in payload.get("parts", []):
            body, html_body = GmailClient._extract_body(part)
            if body or html_body:
                return body, html_body

        return "", None

    @staticmethod
    def _decode_base64(data: str) -> str:
        if not data:
            return ""

        decoded_bytes = base64.urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))
        return decoded_bytes.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_attachment_filenames(payload: Dict[str, Any]) -> List[str]:
        filenames: List[str] = []
        if payload.get("filename"):
            filenames.append(payload["filename"])
        for part in payload.get("parts", []):
            filenames.extend(GmailClient._extract_attachment_filenames(part))
        return filenames

    @staticmethod
    def _parse_internal_date(internal_date: Optional[str]) -> datetime:
        if internal_date:
            try:
                return datetime.utcfromtimestamp(int(internal_date) / 1000)
            except (ValueError, TypeError):
                pass
        return datetime.utcnow()

    @staticmethod
    def _extract_sender_name(sender: str) -> Optional[str]:
        if "<" in sender:
            return sender.split("<")[0].strip().strip('"')
        return None

    @staticmethod
    def _split_addresses(addresses: str) -> List[str]:
        if not addresses:
            return []
        return [address.strip() for address in addresses.split(",") if address.strip()]

    @staticmethod
    def _build_draft_message(to_address: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        message = EmailMessage()
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft: Dict[str, Any] = {"raw": raw}
        if thread_id:
            draft["threadId"] = thread_id
        return draft

