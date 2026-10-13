"""Legacy named coordinator; no peptide-HLA models are implemented."""
import json
import math
import uuid
from typing import Any, Dict, List
from agents.base import PHIGuard
from .models import FrontierPayload, AgentTelemetryAlert, ExecutionStatus
from .engine import FrontierDomainEngine


class HLABindingAffinityAgent:
    """Legacy API name: audits a synthetic scalar rather than binding affinity."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        result = FrontierDomainEngine.evaluate_primary_parameter(payload.primary_metric)
        if result is None:
            return []
        return [AgentTelemetryAlert(
            alert_id=uuid.uuid4().hex[:8], origin_agent="HLABindingAffinityAgent",
            status=ExecutionStatus.ELEVATED_RISK,
            summary=result["summary"], technical_details=result["details"],
            actionable_remediation=result["remediation"],
        )]


class TAPCleavagePredictorAgent:
    """Legacy API name: simple threshold rule, not a cleavage predictor."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        result = FrontierDomainEngine.evaluate_secondary_kinetics(payload.secondary_metric, payload.is_critical_flag)
        if result is None:
            return []
        return [AgentTelemetryAlert(
            alert_id=uuid.uuid4().hex[:8], origin_agent="TAPCleavagePredictorAgent",
            status=ExecutionStatus.CRITICAL_INTERVENTION if payload.is_critical_flag else ExecutionStatus.ELEVATED_RISK,
            summary=result["summary"], technical_details=result["details"],
            actionable_remediation=result["remediation"],
        )]


class ImmunogenicityRankingAgent:
    """Legacy API name: matches descriptor keywords, does not rank peptides."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        result = FrontierDomainEngine.audit_specification_conformance(payload.status_descriptor, payload.attributes)
        if result is None:
            return []
        return [AgentTelemetryAlert(
            alert_id=uuid.uuid4().hex[:8], origin_agent="ImmunogenicityRankingAgent",
            status=ExecutionStatus.ELEVATED_RISK,
            summary=result["summary"], technical_details=result["details"],
            actionable_remediation=result["remediation"],
        )]


class NeoAntigenCoordinator:
    def __init__(self):
        self.sub_1 = HLABindingAffinityAgent()
        self.sub_2 = TAPCleavagePredictorAgent()
        self.sub_3 = ImmunogenicityRankingAgent()
        self.execution_ledger: Dict[str, Dict[str, Any]] = {}

    def process(self, payload: FrontierPayload) -> Dict[str, Any]:
        for value in (payload.primary_metric, payload.secondary_metric):
            if not math.isfinite(value):
                raise ValueError("Metrics must be finite numbers")
        for value in (payload.task_id, payload.target_identifier, payload.status_descriptor):
            PHIGuard.assert_no_phi(value)
        attrs = json.dumps(payload.attributes, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if len(attrs) > 16384:
            raise ValueError("attributes exceeds the 16 KiB input limit")
        PHIGuard.assert_no_phi(attrs)

        alerts: List[AgentTelemetryAlert] = []
        for agent in (self.sub_1, self.sub_2, self.sub_3):
            alerts.extend(agent.audit(payload))

        crit_count = sum(a.status == ExecutionStatus.CRITICAL_INTERVENTION for a in alerts)
        warn_count = sum(a.status == ExecutionStatus.ELEVATED_RISK for a in alerts)
        status = (ExecutionStatus.CRITICAL_INTERVENTION if crit_count else
                  ExecutionStatus.ELEVATED_RISK if warn_count else ExecutionStatus.NOMINAL)
        dossier = {
            "system": "immunopeptidome-neoantigen-agent",
            "domain": "Synthetic rule demonstration",
            "task_id": payload.task_id,
            "target_identifier": payload.target_identifier,
            "overall_status": status.value,
            "total_alerts": len(alerts),
            "critical_count": crit_count,
            "warning_count": warn_count,
            "alerts": [alert.to_dict() for alert in alerts],
            "standard_specification": "No validated immunopeptidomics specification is implemented",
            "consensus_summary": f"Demonstration rules evaluated: {len(alerts)} alerts; {status.value}.",
        }
        self.execution_ledger[payload.task_id] = dossier
        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        PHIGuard.assert_no_phi(query)
        q = query.strip().lower()
        if "status" in q or "ledger" in q:
            return f"Legacy demonstration ledger contains {len(self.execution_ledger)} tasks."
        if "standard" in q or "spec" in q:
            return "No NetMHCpan integration or validated IEDB specifications are implemented."
        return "This is a fixed-response demonstration coordinator; no predictive models are active."
