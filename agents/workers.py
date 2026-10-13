"""Rule-based demonstration workers (thresholds are not clinical ranges)."""
import uuid
from typing import List
from .models import SystemTaskPayload, AgentAlert, UrgencyLevel


class InvariantQCWorker:
    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        if payload.primary_metric <= 25.0:
            return []
        return [AgentAlert(
            alert_id=f"QC-{uuid.uuid4().hex[:6]}", origin_worker="InvariantQCWorker",
            urgency=UrgencyLevel.ELEVATED, summary="Demonstration primary threshold exceeded",
            technical_details=f"Primary metric ({payload.primary_metric:.2f}) > 25 (example threshold).",
            actionable_remediation="Review the entered value and demonstration threshold.",
        )]


class SafetyEscalationWorker:
    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        if not (payload.is_critical_flag or payload.secondary_metric > 12.0):
            return []
        return [AgentAlert(
            alert_id=f"SAFE-{uuid.uuid4().hex[:6]}", origin_worker="SafetyEscalationWorker",
            urgency=UrgencyLevel.CRITICAL_STAT if payload.is_critical_flag else UrgencyLevel.ELEVATED,
            summary="Demo critical flag or secondary threshold triggered",
            technical_details=f"Critical flag={payload.is_critical_flag}; secondary metric={payload.secondary_metric:.2f}.",
            actionable_remediation="Review example inputs; no clinical action is inferred.",
        )]


class ProtocolConformanceWorker:
    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        desc = payload.status_descriptor.upper()
        if not any(flag in desc for flag in ("DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT")):
            return []
        return [AgentAlert(
            alert_id=f"CONF-{uuid.uuid4().hex[:6]}", origin_worker="ProtocolConformanceWorker",
            urgency=UrgencyLevel.ELEVATED, summary="Demonstration descriptor keyword matched",
            technical_details=f"Descriptor {payload.status_descriptor!r} matched an example keyword.",
            actionable_remediation="Inspect the descriptor; this is not a standards compliance determination.",
        )]
