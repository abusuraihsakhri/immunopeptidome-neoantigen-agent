"""Optional FastAPI API for the legacy synthetic rule coordinator."""
from typing import Any, Dict
from .models import FrontierPayload
from .agents import NeoAntigenCoordinator

coordinator = NeoAntigenCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
        from agents.base import SecurityException
    except ImportError:
        return None

    app = FastAPI(
        title="Legacy immunopeptidome rule demonstration",
        description="Example scalar-threshold rules only; no HLA binding prediction.",
        version="2.0.1",
    )

    class TaskRequest(BaseModel):
        task_id: str = Field(default="TASK-2026-001", min_length=1, max_length=120)
        target_identifier: str = Field(default="TARGET-BIO-KEY", min_length=1, max_length=120)
        primary_metric: float = Field(default=28.5, allow_inf_nan=False)
        secondary_metric: float = Field(default=14.2, allow_inf_nan=False)
        status_descriptor: str = Field(default="DISCORDANT_ANOMALY", min_length=1, max_length=120)
        is_critical_flag: bool = True
        attributes: Dict[str, Any] = Field(default_factory=dict)

    class ChatRequest(BaseModel):
        query: str

    @app.get("/health")
    def health():
        return {"status": "HEALTHY", "mode": "synthetic-rules", "version": "2.0.1"}

    @app.post("/api/audit")
    def api_audit(req: TaskRequest):
        try:
            return coordinator.process(FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            ))
        except SecurityException:
            raise HTTPException(status_code=422, detail="Potentially identifying input was blocked.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid task attributes.")

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        try:
            return {"response": coordinator.query_supervisory_chat(req.query)}
        except SecurityException:
            raise HTTPException(status_code=422, detail="Potentially identifying input was blocked.")

    return app
