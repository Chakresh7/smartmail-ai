import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.langgraph.orchestrator import LangGraphOrchestrator
from src.utils.schemas import EmailData


def sample_email():
    return EmailData(
        email_id="e1",
        thread_id="t1",
        subject="Test",
        sender="alice@example.com",
        sender_name="Alice",
        to=["me@example.com"],
        cc=[],
        bcc=[],
        body="Body text",
        html_body=None,
        received_at=datetime.utcnow(),
        is_reply=False,
        labels=[],
        attachments=[],
    )


def test_orchestrator_runs_sequence(monkeypatch):
    import src.nodes as nodes

    monkeypatch.setattr(nodes, "classify_email", lambda e: {"email_id": e.email_id})
    monkeypatch.setattr(nodes, "retrieve_context", lambda e, k=3: [{"doc": "d1"}])
    monkeypatch.setattr(nodes, "summarize_and_extract", lambda e, ctx: {"summary": "ok"})
    monkeypatch.setattr(nodes, "generate_reply_draft", lambda e, ctx: MagicMock(reply_text="reply"))
    monkeypatch.setattr(nodes, "detect_calendar_events", lambda e: [])
    monkeypatch.setattr(nodes, "create_human_review_item", lambda s, reason="": {"review": True})

    orch = LangGraphOrchestrator()
    out = orch.run(sample_email())

    assert out["classification"]["email_id"] == "e1"
    assert out["contexts"][0]["doc"] == "d1"
    assert out["summary"]["summary"] == "ok"
    assert out["reply"].reply_text == "reply"
    assert out["review"]["review"] is True
