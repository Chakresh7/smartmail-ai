from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from src.langgraph.orchestrator import build_default_orchestrator
from src.utils.schemas import EmailData
from src.tools.gmail_tools import GmailClient
import base64
import logging

app = FastAPI(title="SmartMail Orchestrator UI")
orch = build_default_orchestrator()


class EmailPayload(BaseModel):
    # allow arbitrary dict so we can validate via EmailData
    payload: dict


def _serialize(v: Any):
    if hasattr(v, "model_dump"):
        return v.model_dump()
    if hasattr(v, "dict"):
        try:
            return v.dict()
        except Exception:
            return str(v)
    return v


@app.post("/run")
async def run_email(payload: EmailPayload):
    try:
        email = EmailData.model_validate(payload.payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    state = orch.run(email)
    return {k: _serialize(v) for k, v in state.items()}


@app.post("/pubsub")
async def pubsub_push_handler(body: dict):
    """Handle Google Cloud Pub/Sub push messages from Gmail watch.

    Expected format:
    {"message": {"data": "<base64>", ...}, "subscription": "..."}

    This decodes the message, then fetches recent unread emails and runs the orchestrator.
    """
    try:
        msg = body.get("message") or {}
        data_b64 = msg.get("data")
        if data_b64:
            decoded = base64.b64decode(data_b64).decode("utf8")
            logging.info(f"Received Pub/Sub message: {decoded}")
        else:
            logging.info("Received Pub/Sub push with no data")

        # Trigger fetch + run: fetch unread and process
        gmail = GmailClient()
        emails = gmail.fetch_unread_messages(max_results=5)
        results = []
        for e in emails:
            results.append(orch.run(e))

        return {"status": "ok", "processed": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
