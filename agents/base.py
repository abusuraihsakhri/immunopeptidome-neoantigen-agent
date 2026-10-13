"""PHI pattern screening and an in-memory, HMAC-authenticated audit chain.

Pattern screening is a limited safeguard, not comprehensive de-identification.
"""
import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI_PATTERNS = [
    re.compile(r"\bMRN[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:John\s+Doe|Jane\s+Smith|Alice\s+Johnson)\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Identifiable information matched a configured pattern."""


class ResourceLimitExceededException(Exception):
    """Requested work exceeds a configured resource limit."""


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException("Input contains a potentially sensitive identifier.")


class PHIGuard:
    assert_no_phi = staticmethod(assert_no_phi)

    @staticmethod
    def redact_phi(text: str) -> str:
        result = str(text)
        for pattern in PHI_PATTERNS:
            result = pattern.sub("[REDACTED_IDENTIFIER]", result)
        return result


class AuditTrail:
    """In-memory chained HMAC-SHA256 signatures; not durable event storage."""

    GENESIS = "GENESIS_BLOCK_0000000000000000"
    SIGNED_FIELDS = ("audit_id", "timestamp", "actor", "actor_tier", "event_type", "payload_hash", "prev_hash")

    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            resolved_key = secrets.token_hex(32)
            warnings.warn(
                "AUDIT_SECRET_KEY is unset; in-memory audit signatures cannot be verified across restarts.",
                RuntimeWarning,
                stacklevel=2,
            )
        self.secret_key = resolved_key.encode("utf-8") if isinstance(resolved_key, str) else resolved_key
        self.logs: List[Dict[str, Any]] = []

    def _signature(self, entry: Dict[str, Any]) -> str:
        message = "|".join(str(entry[key]) for key in self.SIGNED_FIELDS)
        return hmac.new(self.secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        serialized = json.dumps(details, sort_keys=True, allow_nan=False, ensure_ascii=False)
        for value in (actor, actor_tier, event_type, serialized):
            assert_no_phi(str(value))
        entry = {
            "audit_id": f"AUDIT-{int(time.time() * 1000)}-{len(self.logs) + 1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "actor_tier": actor_tier,
            "event_type": event_type,
            "payload_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "prev_hash": self.logs[-1]["current_hash"] if self.logs else self.GENESIS,
        }
        entry["current_hash"] = self._signature(entry)
        self.logs.append(entry)
        return copy.deepcopy(entry)

    def verify_integrity(self) -> bool:
        prev = self.GENESIS
        for entry in self.logs:
            try:
                if entry["prev_hash"] != prev:
                    return False
                current = entry["current_hash"]
                if not isinstance(current, str) or not hmac.compare_digest(current, self._signature(entry)):
                    return False
                prev = current
            except (KeyError, TypeError, ValueError):
                return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.logs)


GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return GLOBAL_AUDIT.log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return GLOBAL_AUDIT.get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return GLOBAL_AUDIT.verify_integrity()


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return result
