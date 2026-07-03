import argparse
import json
import sys
from time import sleep

from src.langgraph.orchestrator import build_default_orchestrator
from src.tools.gmail_tools import GmailClient
from src.utils.schemas import EmailData


def sample_email() -> EmailData:
    from datetime import datetime

    return EmailData(
        email_id="cli-sample",
        thread_id="cli-thread",
        subject="Sample Run",
        sender="bot@example.com",
        sender_name="Bot",
        to=["me@example.com"],
        cc=[],
        bcc=[],
        body="This is a sample email triggered from the CLI.",
        html_body=None,
        received_at=datetime.utcnow(),
        is_reply=False,
        labels=[],
        attachments=[],
    )


def run_once(orchestrator, email: EmailData):
    state = orchestrator.run(email)
    print(json.dumps(_serialize_state(state), indent=2, default=str))


def _serialize_state(state: dict):
    def conv(v):
        if hasattr(v, "model_dump"):
            return v.model_dump()
        if hasattr(v, "dict"):
            try:
                return v.dict()
            except Exception:
                return str(v)
        return v

    return {k: conv(v) for k, v in state.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description="SmartMail orchestration CLI")
    parser.add_argument("--sample", action="store_true", help="Run orchestrator once with sample email")
    parser.add_argument("--email-file", type=str, help="Path to JSON file with email payload")
    parser.add_argument("--loop", type=int, nargs="?", const=5, help="Run orchestrator in a loop with optional seconds between runs")
    parser.add_argument("--serve", action="store_true", help="Start minimal HTTP server (requires uvicorn & fastapi)")

    args = parser.parse_args(argv)
    orch = build_default_orchestrator()

    if args.serve:
        print("To start the HTTP UI run: \n  uvicorn src.ui.server:app --reload --port 8000")
        return 0

    if args.email_file:
        with open(args.email_file, "r", encoding="utf8") as f:
            payload = json.load(f)
        email = EmailData.model_validate(payload)
        run_once(orch, email)
        return 0

    if args.sample:
        run_once(orch, sample_email())
        return 0

    if args.loop:
        interval = int(args.loop)
        gmail = GmailClient()
        try:
            while True:
                messages = gmail.fetch_unread_messages(max_results=5, label_ids=["INBOX"])
                if not messages:
                    print("No unread messages found.")
                for message in messages:
                    raw = gmail.get_message(message["id"])
                    email = gmail.parse_message(raw)
                    run_once(orch, email)
                    gmail.mark_as_read(message["id"])
                sleep(interval)
        except KeyboardInterrupt:
            print("Stopping loop")
            return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
