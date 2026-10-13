"""FastAPI endpoints for the demonstration audit engine."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(title="Immunopeptidome Audit Demo API", version="2.0.1")


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "immunopeptidome-neoantigen-agent",
            "mode": "generic-rule-demonstration", "version": "2.0.1"}


@app.get("/metrics")
def metrics():
    return {"dossiers_processed_total": len(supervisor.dossier_registry),
            "audit_blocks_total": len(AuditLogger.get_trail()),
            "system_status": "RUNNING"}


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potentially identifying input was blocked.")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid task attributes.")


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potentially identifying input was blocked.")


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# The same static console also runs on GitHub Pages without a backend.
_ROOT = Path(__file__).resolve().parent.parent
if (_ROOT / "web").is_dir():
    app.mount("/web", StaticFiles(directory=str(_ROOT / "web")), name="web")
if (_ROOT / "index.html").is_file():
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(_ROOT / "index.html")
