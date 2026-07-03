"""
Google Calendar API wrapper for SmartMail AI.

This module provides abstractions for calendar authorization,
availability checking, and event creation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.config import settings
from src.utils.schemas import CalendarEventData
from src.utils.helpers import SmartMailException


SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class CalendarAPIError(SmartMailException):
    """Raised when the Calendar API client encounters an error."""
    pass


class CalendarClient:
    """Client for Google Calendar API operations."""

    def __init__(self, credentials_path: str = settings.google_calendar_credentials_path):
        self.credentials_path = credentials_path
        self.creds: Optional[Credentials] = None
        self.service = self._authorize()

    def _authorize(self) -> Any:
        """Authorize and return a Google Calendar API service object."""
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
        return build("calendar", "v3", credentials=creds)

    def create_event(self, event: CalendarEventData) -> Dict[str, Any]:
        """Create a calendar event from a CalendarEventData model."""
        try:
            event_body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": event.timezone,
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": event.timezone,
                },
                "attendees": [{"email": email} for email in event.attendees],
                "conferenceData": {},
                "source": {
                    "title": "SmartMail AI",
                    "url": "https://smartmail.ai",
                },
            }

            if event.location:
                event_body["location"] = event.location

            response = self.service.events().insert(
                calendarId="primary",
                body=event_body,
                sendUpdates="none",
            ).execute()
            return response
        except Exception as exc:
            raise CalendarAPIError(f"Error creating calendar event: {exc}") from exc

    def find_free_slots(
        self,
        calendar_id: str = "primary",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        duration_minutes: int = 30,
    ) -> List[Dict[str, Any]]:
        """Find available time slots in the calendar."""
        try:
            if start is None:
                start = datetime.utcnow()
            if end is None:
                end = start + timedelta(days=7)

            body = {
                "timeMin": start.isoformat() + "Z",
                "timeMax": end.isoformat() + "Z",
                "items": [{"id": calendar_id}],
            }
            response = self.service.freebusy().query(body=body).execute()
            busy_periods = response.get("calendars", {}).get(calendar_id, {}).get("busy", [])

            free_slots: List[Dict[str, Any]] = []
            current = start
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                if (busy_start - current).total_seconds() >= duration_minutes * 60:
                    free_slots.append({
                        "start": current.isoformat(),
                        "end": busy_start.isoformat(),
                    })
                current = max(current, busy_end)

            if (end - current).total_seconds() >= duration_minutes * 60:
                free_slots.append({"start": current.isoformat(), "end": end.isoformat()})

            return free_slots
        except Exception as exc:
            raise CalendarAPIError(f"Error finding free slots: {exc}") from exc

    def get_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve events from a calendar."""
        try:
            params: Dict[str, Any] = {
                "calendarId": calendar_id,
                "singleEvents": True,
                "orderBy": "startTime",
                "maxResults": max_results,
            }
            if time_min:
                params["timeMin"] = time_min.isoformat() + "Z"
            if time_max:
                params["timeMax"] = time_max.isoformat() + "Z"

            response = self.service.events().list(**params).execute()
            return response.get("items", [])
        except Exception as exc:
            raise CalendarAPIError(f"Error retrieving calendar events: {exc}") from exc

    def update_event(self, event_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            response = self.service.events().patch(
                calendarId="primary",
                eventId=event_id,
                body=changes,
                sendUpdates="none",
            ).execute()
            return response
        except Exception as exc:
            raise CalendarAPIError(f"Error updating calendar event {event_id}: {exc}") from exc

    def delete_event(self, event_id: str) -> None:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId="primary",
                eventId=event_id,
                sendUpdates="none",
            ).execute()
        except Exception as exc:
            raise CalendarAPIError(f"Error deleting calendar event {event_id}: {exc}") from exc

