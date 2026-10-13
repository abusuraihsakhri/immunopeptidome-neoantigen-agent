"""Legacy domain coordinator CLI (generic threshold demonstration)."""
import argparse
import csv
import sys
from agents.csv_utils import parse_csv_bool
from .models import FrontierPayload
from .agents import NeoAntigenCoordinator

coordinator = NeoAntigenCoordinator()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="immunopeptidome-neoantigen-engine",
                                     description="Experimental coordinator; no NetMHCpan model is bundled")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--task-id", default="TASK-2026-001")
    audit.add_argument("--target", default="TARGET-GEN-01")
    audit.add_argument("--primary", type=float, default=29.4)
    audit.add_argument("--secondary", type=float, default=15.1)
    audit.add_argument("--critical", action="store_true")
    audit.add_argument("--status", default="DISCORDANT")
    chat = subparsers.add_parser("chat")
    chat.add_argument("query", nargs="+")
    batch = subparsers.add_parser("batch")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    serve = subparsers.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.command == "audit":
        dossier = coordinator.process(FrontierPayload(
            task_id=args.task_id, target_identifier=args.target,
            primary_metric=args.primary, secondary_metric=args.secondary,
            status_descriptor=args.status, is_critical_flag=args.critical,
        ))
        print(f"Demonstration task {dossier['task_id']}: {dossier['overall_status']}")
        for alert in dossier["alerts"]:
            print(f"{alert['origin_agent']}: {alert['summary']}")
        return 0

    if args.command == "chat":
        print(coordinator.query_supervisory_chat(" ".join(args.query)))
        return 0

    if args.command == "batch":
        with open(args.input, "r", encoding="utf-8-sig", newline="") as infile:
            reader = csv.DictReader(infile)
            headers = list(reader.fieldnames or [])
            if not headers or len(set(headers)) != len(headers):
                raise ValueError("CSV headers must be present and unique")
            mandatory = {"task_id", "target_identifier", "primary_metric", "secondary_metric",
                         "status_descriptor", "is_critical_flag"}
            if not mandatory.issubset(headers):
                raise ValueError("Missing required CSV columns")
            rows = list(reader)
        fields = headers + [name for name in ("overall_status", "total_alerts", "critical_count", "consensus_summary")
                            if name not in headers]
        output = []
        for line, row in enumerate(rows, 2):
            if None in row:
                raise ValueError(f"Row {line} has too many fields")
            try:
                dossier = coordinator.process(FrontierPayload(
                    task_id=row["task_id"], target_identifier=row["target_identifier"],
                    primary_metric=float(row["primary_metric"]),
                    secondary_metric=float(row["secondary_metric"]),
                    status_descriptor=row["status_descriptor"],
                    is_critical_flag=parse_csv_bool(row["is_critical_flag"]),
                ))
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid CSV row {line}: {error}") from error
            output.append(dict(row, **{key: dossier[key] for key in
                                      ("overall_status", "total_alerts", "critical_count", "consensus_summary")}))
        with open(args.output, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(output)
        print(f"Processed {len(output)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from .server import create_app
        app = create_app()
        if app is None:
            raise RuntimeError("Install optional API dependencies first")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
