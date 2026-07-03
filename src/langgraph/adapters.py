from typing import Any, List, Dict
from src.utils.schemas import EmailData
import src.nodes as nodes


def _to_dict(v: Any):
    from unittest.mock import MagicMock

    # Return simple types as-is
    if isinstance(v, (str, int, float, bool, dict, list, tuple)):
        return v

    # Preserve MagicMock objects (used in tests)
    if isinstance(v, MagicMock):
        return v

    if hasattr(v, "model_dump"):
        try:
            return v.model_dump()
        except Exception:
            pass
    if hasattr(v, "dict"):
        try:
            return v.dict()
        except Exception:
            return str(v)
    return v


def classify_adapter(email: EmailData) -> Dict[str, Any]:
    res = nodes.classify_email(email)
    return _to_dict(res)


def retrieve_adapter(email: EmailData, k: int = 3) -> List[Dict[str, Any]]:
    res = nodes.retrieve_context(email, k=k)
    return [_to_dict(r) for r in res]


def summarize_adapter(email: EmailData, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    res = nodes.summarize_and_extract(email, contexts)
    return _to_dict(res)


def reply_adapter(email: EmailData, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    res = nodes.generate_reply_draft(email, contexts)
    return _to_dict(res)


def calendar_adapter(email: EmailData) -> List[Dict[str, Any]]:
    res = nodes.detect_calendar_events(email)
    return [_to_dict(r) for r in res]


def human_review_adapter(state: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    # nodes.create_human_review_item expects a GraphState-like object
    from types import SimpleNamespace

    ns = SimpleNamespace(
        email=None,
        email_id=state.get("email_id"),
        classification=state.get("classification"),
        reply_draft=state.get("reply"),
        calendar_events=state.get("events"),
    )
    res = nodes.create_human_review_item(ns, reason)
    return _to_dict(res)
