"""Orchestrates rule-based audit workers and in-memory dossiers."""
import json
import uuid
from typing import Dict, List
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, AgentAlert, ConsensusDossier, UrgencyLevel, SystemIntegrityStatus
from .workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from .llm_factory import LLMFactory


class SystemSupervisor:
    def __init__(self, model_provider: str = "mock"):
        self.qc_worker = InvariantQCWorker()
        self.safety_worker = SafetyEscalationWorker()
        self.conformance_worker = ProtocolConformanceWorker()
        self.llm = LLMFactory.create(model_provider, system_name="Immunopeptidome Neoantigen Agent")
        self.dossier_registry: Dict[str, ConsensusDossier] = {}

    def process_task(self, payload: SystemTaskPayload, actor: str = "SystemSupervisor") -> ConsensusDossier:
        for value in (payload.task_id, payload.target_identifier, payload.status_descriptor):
            PHIGuard.assert_no_phi(value)
        attributes_json = json.dumps(payload.attributes, sort_keys=True, allow_nan=False, ensure_ascii=False)
        if len(attributes_json) > 16384:
            raise ValueError("attributes exceeds the 16 KiB input limit")
        PHIGuard.assert_no_phi(attributes_json)

        all_alerts: List[AgentAlert] = []
        all_alerts.extend(self.qc_worker.evaluate(payload))
        all_alerts.extend(self.safety_worker.evaluate(payload))
        all_alerts.extend(self.conformance_worker.evaluate(payload))

        crit_count = sum(a.urgency == UrgencyLevel.CRITICAL_STAT for a in all_alerts)
        elev_count = sum(a.urgency == UrgencyLevel.ELEVATED for a in all_alerts)
        if crit_count:
            urgency, integrity = UrgencyLevel.CRITICAL_STAT, SystemIntegrityStatus.RECALIBRATION_REQUIRED
        elif elev_count:
            urgency, integrity = UrgencyLevel.ELEVATED, SystemIntegrityStatus.DISCORDANT
        else:
            urgency, integrity = UrgencyLevel.ROUTINE, SystemIntegrityStatus.VALIDATED

        audit_entry = AuditLogger.log(
            actor, "supervisor", "TASK_EVALUATION_COMPLETED",
            {"task_id": payload.task_id, "target_identifier": payload.target_identifier,
             "overall_urgency": urgency.value, "total_alerts": len(all_alerts)},
        )
        dossier = ConsensusDossier(
            dossier_id=f"DOSSIER-{uuid.uuid4().hex[:8].upper()}",
            task_id=payload.task_id,
            target_identifier=payload.target_identifier,
            overall_urgency=urgency,
            integrity_status=integrity,
            total_alerts=len(all_alerts),
            critical_alerts_count=crit_count,
            alerts=all_alerts,
            consensus_summary=f"Rule-based evaluation completed: {urgency.value}; {len(all_alerts)} alerts.",
            audit_hash=audit_entry["current_hash"],
        )
        self.dossier_registry[dossier.dossier_id] = dossier
        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        PHIGuard.assert_no_phi(query)
        return self.llm.invoke(f"Supervisor inquiry: {query}")
