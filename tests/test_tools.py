import pytest
from unittest.mock import MagicMock, patch

from src.tools.gmail_tools import GmailClient, GmailAPIError
from src.tools.calendar_tools import CalendarClient, CalendarAPIError
from src.utils.schemas import CalendarEventData
from datetime import datetime, timedelta


class DummyCredentials:
    def __init__(self):
        self.valid = True
        self.expired = False
        self.refresh_token = None

    def to_json(self):
        return "{}"


@pytest.fixture(autouse=True)
def patch_credentials(monkeypatch):
    monkeypatch.setattr('src.tools.gmail_tools.Credentials.from_authorized_user_file', lambda path, scopes: DummyCredentials())
    monkeypatch.setattr('src.tools.calendar_tools.Credentials.from_authorized_user_file', lambda path, scopes: DummyCredentials())
    monkeypatch.setattr('src.tools.gmail_tools.InstalledAppFlow.from_client_secrets_file', lambda path, scopes: MagicMock(run_local_server=lambda port: DummyCredentials()))
    monkeypatch.setattr('src.tools.calendar_tools.InstalledAppFlow.from_client_secrets_file', lambda path, scopes: MagicMock(run_local_server=lambda port: DummyCredentials()))
    monkeypatch.setattr('src.tools.gmail_tools.build', lambda service_name, version, credentials: MagicMock())
    monkeypatch.setattr('src.tools.calendar_tools.build', lambda service_name, version, credentials: MagicMock())


def test_gmail_client_initializes():
    client = GmailClient(credentials_path='dummy.json')
    assert client.service is not None


def test_calendar_client_initializes():
    client = CalendarClient(credentials_path='dummy.json')
    assert client.service is not None


def test_gmail_fetch_unread_messages_calls_api(monkeypatch):
    mock_service = MagicMock()
    mock_messages = MagicMock()
    mock_messages.list.return_value.execute.return_value = {'messages': [{'id': '123'}]}
    mock_service.users.return_value.messages.return_value = mock_messages

    with patch('src.tools.gmail_tools.build', return_value=mock_service):
        client = GmailClient(credentials_path='dummy.json')
        result = client.fetch_unread_messages(max_results=1)
        assert result == [{'id': '123'}]


def test_gmail_get_message_calls_api(monkeypatch):
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {'id': '123', 'payload': {'headers': []}}

    with patch('src.tools.gmail_tools.build', return_value=mock_service):
        client = GmailClient(credentials_path='dummy.json')
        result = client.get_message('123')
        assert result['id'] == '123'


def test_calendar_get_events_calls_api(monkeypatch):
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {'items': [{'id': 'event1'}]}
    with patch('src.tools.calendar_tools.build', return_value=mock_service):
        client = CalendarClient(credentials_path='dummy.json')
        events = client.get_events()
        assert events == [{'id': 'event1'}]


def test_calendar_create_event_builds_request(monkeypatch):
    mock_service = MagicMock()
    mock_service.events.return_value.insert.return_value.execute.return_value = {'id': 'event1', 'summary': 'Test'}
    with patch('src.tools.calendar_tools.build', return_value=mock_service):
        client = CalendarClient(credentials_path='dummy.json')
        event = CalendarEventData(
            title='Test Event',
            description='A test event',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            attendees=['test@example.com'],
            location='Office',
            timezone='UTC',
            source_email_id='email_123',
            confidence=0.95,
            requires_confirmation=True,
        )
        response = client.create_event(event)
        assert response['id'] == 'event1'


def test_gmail_save_draft_uses_original_message(monkeypatch):
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        'id': '123',
        'threadId': 'thread_1',
        'payload': {'headers': [{'name': 'From', 'value': 'sender@example.com'}, {'name': 'Subject', 'value': 'Test'}]}
    }
    mock_service.users.return_value.drafts.return_value.create.return_value.execute.return_value = {'id': 'draft1'}

    with patch('src.tools.gmail_tools.build', return_value=mock_service):
        client = GmailClient(credentials_path='dummy.json')
        result = client.save_draft('123', 'Hello')
        assert result['id'] == 'draft1'


def test_gmail_mark_as_read_calls_modify(monkeypatch):
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}
    with patch('src.tools.gmail_tools.build', return_value=mock_service):
        client = GmailClient(credentials_path='dummy.json')
        client.mark_as_read('123')
        mock_service.users.return_value.messages.return_value.modify.assert_called_once()
