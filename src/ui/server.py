from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from src.langgraph.orchestrator import build_default_orchestrator
from src.utils.schemas import EmailData

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
