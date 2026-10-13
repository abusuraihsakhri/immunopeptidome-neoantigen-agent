"""Command-line interface for the rule-based audit engine."""
import argparse
import csv
import sys
from agents.csv_utils import parse_csv_bool
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="immunopeptidome-neoantigen-agent", description="Generic task audit demonstration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Evaluate a demonstration task")
    audit.add_argument("--task-id", default="TASK-2026-001")
    audit.add_argument("--target", default="KEY-TARGET-01")
    audit.add_argument("--primary", type=float, default=28.5)
    audit.add_argument("--secondary", type=float, default=14.2)
    audit.add_argument("--critical", action="store_true")
    audit.add_argument("--status", default="DISCORDANT")
    chat = subparsers.add_parser("chat", help="Query the mock supervisor (no external model)")
    chat.add_argument("query", nargs="+")
    batch = subparsers.add_parser("batch", help="Evaluate a CSV batch")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    subparsers.add_parser("verify-audit", help="Verify the current in-memory HMAC audit chain")
    serve = subparsers.add_parser("serve", help="Launch FastAPI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id, target_identifier=args.target,
            primary_metric=args.primary, secondary_metric=args.secondary,
            status_descriptor=args.status, is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("Generic rule-based demonstration (not an HLA-binding prediction)")
        print(f"Task: {dossier.task_id} | Urgency: {dossier.overall_urgency.value} | Alerts: {dossier.total_alerts}")
        for alert in dossier.alerts:
            print(f"{alert.origin_worker}: {alert.summary}")
        print(f"In-memory audit signature: {dossier.audit_hash}")
        return 0

    if args.command == "chat":
        print(supervisor.query_supervisory_chat(" ".join(args.query)))
        return 0

    if args.command == "verify-audit":
        print(f"Audit entries: {len(AuditLogger.get_trail())} | Verified: {AuditLogger.verify_integrity()}")
        return 0 if AuditLogger.verify_integrity() else 1

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig", newline="") as infile:
            reader = csv.DictReader(infile)
            fieldnames = list(reader.fieldnames or [])
            if not fieldnames or len(set(fieldnames)) != len(fieldnames):
                raise ValueError("CSV headers must be present and unique")
            mandatory = {"task_id", "target_identifier", "primary_metric", "secondary_metric",
                         "status_descriptor", "is_critical_flag"}
            if not mandatory.issubset(fieldnames):
                raise ValueError("Missing required CSV columns")
            rows = list(reader)

        derived = ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        output_fields = fieldnames + [key for key in derived if key not in fieldnames]
        results = []
        for number, row in enumerate(rows, start=2):
            if None in row:
                raise ValueError(f"Row {number} has too many fields")
            try:
                payload = SystemTaskPayload(
                    task_id=row["task_id"], target_identifier=row["target_identifier"],
                    primary_metric=float(row["primary_metric"]),
                    secondary_metric=float(row["secondary_metric"]),
                    status_descriptor=row["status_descriptor"],
                    is_critical_flag=parse_csv_bool(row["is_critical_flag"]),
                )
                dossier = supervisor.process_task(payload)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid CSV row {number}: {error}") from error
            item = dict(row)
            item.update(overall_urgency=dossier.overall_urgency.value,
                        integrity_status=dossier.integrity_status.value,
                        total_alerts=dossier.total_alerts,
                        audit_hash=dossier.audit_hash)
            results.append(item)

        with open(args.output, mode="w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows(results)
        print(f"Processed {len(results)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
