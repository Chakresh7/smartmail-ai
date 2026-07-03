from typing import List, Dict, Any
from src.utils.schemas import EmailData
import src.nodes as nodes


class LangGraphOrchestrator:
    """A lightweight LangGraph-like orchestrator that composes existing node functions.

    This is intentionally framework-free so it works without installing external libs.
    The `pipeline` is a list of step keys that map to node functions.
    """

    DEFAULT_PIPELINE = [
        "classify",
        "retrieve",
        "summarize",
        "reply",
        "calendar",
        "human_review",
    ]

    def __init__(self, pipeline: List[str] | None = None):
        self.pipeline = pipeline or self.DEFAULT_PIPELINE

    def run(self, email: EmailData) -> Dict[str, Any]:
        state: Dict[str, Any] = {"email_id": email.email_id}

        for step in self.pipeline:
            if step == "classify" and hasattr(nodes, "classify_email"):
                state["classification"] = nodes.classify_email(email)

            if step == "retrieve" and hasattr(nodes, "retrieve_context"):
                state["contexts"] = nodes.retrieve_context(email, k=3)

            if step == "summarize" and hasattr(nodes, "summarize_and_extract"):
                state["summary"] = nodes.summarize_and_extract(email, state.get("contexts", []))

            if step == "reply" and hasattr(nodes, "generate_reply_draft"):
                state["reply"] = nodes.generate_reply_draft(email, state.get("contexts", []))

            if step == "calendar" and hasattr(nodes, "detect_calendar_events"):
                state["events"] = nodes.detect_calendar_events(email)

            if step == "human_review" and hasattr(nodes, "create_human_review_item"):
                state["review"] = nodes.create_human_review_item(state, reason="auto-orchestrator")

        return state


def build_default_orchestrator() -> LangGraphOrchestrator:
    return LangGraphOrchestrator()
