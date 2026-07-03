import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.utils.schemas import EmailData
from config.config import settings

from src.nodes import classify_email, generate_reply_draft, summarize_and_extract


def sample_email():
    return EmailData(
        email_id="e1",
        thread_id="t1",
        subject="Test meeting request",
        sender="alice@example.com",
        sender_name="Alice",
        to=["me@example.com"],
        cc=[],
        bcc=[],
        body="Can we schedule a meeting next week to discuss the project?",
        html_body=None,
        received_at=datetime.utcnow(),
        is_reply=False,
        labels=[],
        attachments=[],
    )


def test_classifier_heuristic(monkeypatch):
    # Force dry run fallback
    monkeypatch.setattr(settings, "dry_run_mode", True)
    email = sample_email()
    result = classify_email(email)
    assert result.email_id == "e1"
    assert result.email_type is not None


def test_classifier_parses_openai_output(monkeypatch):
    # Provide a fake OpenAI response shape with output->content->text containing JSON
    fake_resp = MagicMock()
    fake_resp.output = [
        {"content": [{"text": '{"email_type":"general_email","type_confidence":0.9,"priority":"normal","priority_confidence":0.8,"intent":"informational","intent_confidence":0.85,"reasoning":"ok"}'}]}
    ]

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        class responses:
            @staticmethod
            def create(**kwargs):
                return fake_resp

    monkeypatch.setattr("src.nodes.classifier.OpenAI", lambda **kwargs: FakeClient())
    monkeypatch.setattr(settings, "dry_run_mode", False)
    monkeypatch.setattr(settings, "openai_api_key", "x")

    res = classify_email(sample_email())
    assert res.type_confidence >= 0.8


def test_reply_generator_parses_choices(monkeypatch):
    fake_resp = {"choices": [{"text": "This is a generated reply."}]}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        class responses:
            @staticmethod
            def create(**kwargs):
                return fake_resp

    monkeypatch.setattr("src.nodes.reply_generator.OpenAI", lambda **kwargs: FakeClient())
    monkeypatch.setattr(settings, "dry_run_mode", False)
    monkeypatch.setattr(settings, "openai_api_key", "x")

    draft = generate_reply_draft(sample_email(), [])
    assert "generated reply" in draft.reply_text.lower()


def test_summarizer_parses_json(monkeypatch):
    fake_resp = MagicMock()
    fake_resp.output = [{"content": [{"text": '{"summary":"Short summary","key_points":["p1"],"sentiment":"neutral","entities":{}}'}]}]

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        class responses:
            @staticmethod
            def create(**kwargs):
                return fake_resp

    monkeypatch.setattr("src.nodes.summarizer.OpenAI", lambda **kwargs: FakeClient())
    monkeypatch.setattr(settings, "dry_run_mode", False)
    monkeypatch.setattr(settings, "openai_api_key", "x")

    summary = summarize_and_extract(sample_email(), [])
    assert summary.summary.startswith("Short summary") or summary.key_points
