"""Legacy coordinator's example threshold rules; not an HLA-binding model."""
from typing import Any, Dict, Optional


class FrontierDomainEngine:
    STANDARD = "Synthetic demonstration (no validated immunopeptidomics reference)"
    PRIMARY_BOUND = 25.0
    SECONDARY_BOUND = 10.0

    @classmethod
    def evaluate_primary_parameter(cls, value: float) -> Optional[Dict[str, Any]]:
        if value <= cls.PRIMARY_BOUND:
            return None
        return {
            "summary": "Primary example threshold exceeded",
            "details": f"Parameter {value:.3f} exceeds synthetic threshold {cls.PRIMARY_BOUND:.1f}.",
            "remediation": "Review demonstration input; no binding affinity is calculated.",
        }

    @classmethod
    def evaluate_secondary_kinetics(cls, value: float, is_critical: bool) -> Optional[Dict[str, Any]]:
        if value <= cls.SECONDARY_BOUND and not is_critical:
            return None
        return {
            "summary": "Secondary example condition triggered",
            "details": f"Secondary parameter {value:.3f}; critical flag={is_critical}.",
            "remediation": "Review the example case; no biochemical prediction is calculated.",
        }

    @classmethod
    def audit_specification_conformance(cls, descriptor: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not any(flag in str(descriptor).upper() for flag in ("VIOLATION", "DISCORDANT", "ANOMALY", "MUTANT", "LEAK")):
            return None
        return {
            "summary": "Demonstration descriptor keyword matched",
            "details": f"Descriptor {descriptor!r} matched a configured keyword, not a reference-standard test.",
            "remediation": "Review the demonstration descriptor.",
        }
