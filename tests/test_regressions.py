"""Regression coverage for security, CSV semantics and static console."""
import csv
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.csv_utils import parse_csv_bool
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor
from cli import main as main_cli
from neoantigen_predictor.cli import main as legacy_cli


def test_audit_hmac_detects_modified_entry():
    trail = AuditTrail(secret_key="test-key")
    trail.log("Supervisor", "system", "EVENT", {"data": 1})
    trail.log("Supervisor", "system", "EVENT", {"data": 2})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "Impostor"
    assert not trail.verify_integrity()


def test_audit_chain_and_public_result_are_defensive_copies():
    trail = AuditTrail(secret_key="test-key")
    result = trail.log("Supervisor", "system", "EVENT", {"data": 1})
    result["actor"] = "Mutated"
    exposed = trail.get_trail()
    exposed[0]["current_hash"] = "0" * 64
    assert trail.verify_integrity()
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_nested_phi_is_rejected_before_logging():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="demo", target_identifier="example", primary_metric=1.0,
                                attributes={"nested": {"contact": "someone@example.org"}})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_nonfinite_metrics_rejected():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="demo", target_identifier="target", primary_metric=value)
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="demo", target_identifier="target", primary_metric=1, secondary_metric=value)


@pytest.mark.parametrize("value,expected", [("False", False), ("false", False), ("0", False),
                                             ("no", False), ("TRUE", True), ("yes", True), ("1", True)])
def test_boolean_parser(value, expected):
    assert parse_csv_bool(value) is expected


def test_boolean_parser_rejects_unknown():
    with pytest.raises(ValueError):
        parse_csv_bool("maybe")


@pytest.mark.parametrize("entrypoint,status_column", [
    (main_cli, "overall_urgency"),
    (legacy_cli, "overall_status"),
])
def test_csv_false_does_not_trigger_critical(tmp_path, entrypoint, status_column):
    source = tmp_path / "input.csv"
    dest = tmp_path / "output.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        "T1,TARGET,1,2,False,NOMINAL\n"
        "T2,TARGET,1,2,True,NOMINAL\n", encoding="utf-8",
    )
    assert entrypoint(["batch", "-i", str(source), "-o", str(dest)]) == 0
    with dest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert "CRITICAL" not in rows[0][status_column]
    assert "CRITICAL" in rows[1][status_column]


def test_mock_does_not_claim_external_validation():
    response = LLMFactory.create("openai").invoke("Sample status?")
    assert "MOCK" in response
    assert "No language model" in response


def test_api_and_static_entrypoint():
    from fastapi.testclient import TestClient
    from agents.api import app
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200
        assert client.get("/web/app.js").status_code == 200
        assert client.get("/web/styles.css").status_code == 200
        payload = dict(task_id="A", target_identifier="B", primary_metric=5,
                       secondary_metric=2, status_descriptor="NOMINAL", is_critical_flag=False)
        ok = client.post("/api/audit", json=payload)
        assert ok.status_code == 200
        assert ok.json()["overall_urgency"] == UrgencyLevel.ROUTINE.value
        assert client.get("/api/audit/logs").json()["verified"] is True
        malicious = dict(payload, attributes={"nested": "patient@sample.org"})
        assert client.post("/api/audit", json=malicious).status_code == 422
        nonfinite = dict(payload, primary_metric="NaN")
        assert client.post("/api/audit", json=nonfinite).status_code == 422
