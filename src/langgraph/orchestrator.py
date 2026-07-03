from typing import List, Dict, Any
from src.utils.schemas import EmailData

try:
    import src.langgraph.adapters as lg_adapters
except Exception:
    lg_adapters = None

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
            if step == "classify":
                if lg_adapters and hasattr(lg_adapters, "classify_adapter"):
                    state["classification"] = lg_adapters.classify_adapter(email)
                elif hasattr(nodes, "classify_email"):
                    state["classification"] = nodes.classify_email(email)

            if step == "retrieve":
                if lg_adapters and hasattr(lg_adapters, "retrieve_adapter"):
                    state["contexts"] = lg_adapters.retrieve_adapter(email, k=3)
                elif hasattr(nodes, "retrieve_context"):
                    state["contexts"] = nodes.retrieve_context(email, k=3)

            if step == "summarize":
                if lg_adapters and hasattr(lg_adapters, "summarize_adapter"):
                    state["summary"] = lg_adapters.summarize_adapter(email, state.get("contexts", []))
                elif hasattr(nodes, "summarize_and_extract"):
                    state["summary"] = nodes.summarize_and_extract(email, state.get("contexts", []))

            if step == "reply":
                if lg_adapters and hasattr(lg_adapters, "reply_adapter"):
                    state["reply"] = lg_adapters.reply_adapter(email, state.get("contexts", []))
                elif hasattr(nodes, "generate_reply_draft"):
                    state["reply"] = nodes.generate_reply_draft(email, state.get("contexts", []))

            if step == "calendar":
                if lg_adapters and hasattr(lg_adapters, "calendar_adapter"):
                    state["events"] = lg_adapters.calendar_adapter(email)
                elif hasattr(nodes, "detect_calendar_events"):
                    state["events"] = nodes.detect_calendar_events(email)

            if step == "human_review":
                if lg_adapters and hasattr(lg_adapters, "human_review_adapter"):
                    state["review"] = lg_adapters.human_review_adapter(state, reason="auto-orchestrator")
                elif hasattr(nodes, "create_human_review_item"):
                    state["review"] = nodes.create_human_review_item(state, reason="auto-orchestrator")

        return state


def build_default_orchestrator() -> LangGraphOrchestrator:
    return LangGraphOrchestrator()
