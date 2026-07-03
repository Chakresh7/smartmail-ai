try:
    import streamlit as st
except Exception:
    st = None

import json
from src.langgraph.orchestrator import build_default_orchestrator
from src.utils.schemas import EmailData
from src.ui.graph import build_flow_dot


def _sample_payload():
    return {
        "email_id": "streamlit-sample",
        "thread_id": "t1",
        "subject": "Streamlit Sample",
        "sender": "bot@example.com",
        "sender_name": "Bot",
        "to": ["me@example.com"],
        "cc": [],
        "bcc": [],
        "body": "Please review the attached proposal.",
        "html_body": None,
        "received_at": "2026-01-01T00:00:00",
        "is_reply": False,
        "labels": [],
        "attachments": [],
    }


def main():
    if st is None:
        print("Streamlit is not installed. To run the UI install streamlit and run:\n  streamlit run src/ui/streamlit_app.py")
        return

    st.title("SmartMail Orchestrator")
    st.sidebar.header("Run Options")
    payload_text = st.sidebar.text_area("Email JSON", value=json.dumps(_sample_payload(), indent=2), height=300)
    run_btn = st.sidebar.button("Run Orchestrator")

    if run_btn:
        try:
            payload = json.loads(payload_text)
            email = EmailData.model_validate(payload)
        except Exception as exc:
            st.error(f"Invalid payload: {exc}")
            return

        orch = build_default_orchestrator()
        state = orch.run(email)

        st.subheader("Orchestrator State")
        st.json({k: str(v) for k, v in state.items()})

        st.subheader("Flow Graph")
        dot = build_flow_dot(state)
        st.graphviz_chart(dot)


if __name__ == "__main__":
    main()
