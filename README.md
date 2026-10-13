# Immunopeptidome Neoantigen Agent

A **rule-based task-auditing demonstration** with two Python coordinators, a FastAPI backend, and a browser-only console. The repository name reflects its intended research domain, **not** an implemented immunopeptidomics model.

> **Research scope:** The code currently does **not** run NetMHCpan, estimate HLA-I or HLA-II binding affinity, infer antigen presentation, rank immunogenicity, or validate clinical decisions. Thresholds and alerts are synthetic examples, not scientific reference ranges. Do not use outputs for patient care or neoantigen selection.

## Browser console

Open [`index.html`](index.html) in a modern browser, or serve the project through FastAPI. Single-task rules execute entirely in JavaScript by default; batch CSV import and export also run entirely in the browser. The console provides input validation, an audit-like JSON summary, and file downloads without external libraries.

On a Python server, select **Connected FastAPI** to send a single task to `/api/audit`. In this mode, the backend creates a genuine in-memory HMAC-SHA256 audit-chain entry. Local browser mode **does not** create signed audit records.

## Demonstration rule set

| Input | Rule | Outcome |
| --- | --- | --- |
| Primary metric | Value > 25 | Elevated example alert |
| Secondary metric | Value > 12 | Elevated example alert |
| Critical flag | Checked/true | Critical example alert |
| Descriptor | Contains DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL or REJECT | Elevated example alert |

The legacy `neoantigen_predictor` coordinator uses separate example thresholds (primary >25 and secondary >10); neither is a model of HLA binding. Existing entry points remain available for compatibility.

## Python CLI and API

Requires Python 3.9 or later.

```bash
python -m pip install -e ".[api]"
python cli.py audit --task-id DEMO-1 --target EXAMPLE --primary 28 --secondary 3 --status NOMINAL
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the same console with optional backend mode. FastAPI also exposes `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. OpenAPI schema is available at `/docs`.

The separately retained legacy CLI is:

```bash
python -m neoantigen_predictor.cli audit
python -m neoantigen_predictor.cli batch -i sample.csv -o results.csv
```

**CSV columns:** `task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor`. Use literal `true` or `false` (also `1/0`, `yes/no`). The browser permits up to 2 MiB and 2,000 records per batch.

## Privacy and security

- Browser local mode processes data in-memory, without server submission or browser persistence. Manual downloads contain the entered values.
- Connected API mode transmits data to the selected FastAPI server. There is no built-in authentication: bind only to loopback and do not expose this demonstration to the public internet.
- A **limited regex screen** detects some common personal identifiers. It is not a validated PHI de-identification process or evidence of HIPAA compliance. Use synthetic or properly de-identified data.
- Backend audit entries include payload digests and chained HMAC-SHA256 signatures; the verifier checks both signatures and links. Audit entries and the signing key are **in-memory only** by default. They are not durable evidence of provenance.
- Set `AUDIT_SECRET_KEY` to a securely generated value for stable signing credentials, but records are still not persisted. Do not commit secrets to Git.
- Model-provider labels are currently deterministic **mock responses**; external language-model adapters are not implemented.

## Testing

```bash
python -m pip install -e ".[api,dev]"
python -m pytest -q
node --check web/app.js
```

GitHub Actions tests Python 3.10–3.12, compilation, static JavaScript syntax, and the installed console entry point.

## Deployment

The included workflow attempts to publish the static console through GitHub Pages. Static hosting runs the **JavaScript rules only**, not FastAPI or a Python interpreter. Pages activation and the deployed URL must be checked in repository settings and workflow output.

For local Docker development:

```bash
docker compose up --build
```

The container serves the FastAPI backend at `http://127.0.0.1:8000/` through a loopback-only host port binding.

## Technology, compatibility and license

Python, Pydantic v2, optional FastAPI/Uvicorn, and standard HTML/CSS/JavaScript. The browser console uses modern JavaScript (including `replaceAll`) and is intended for current Chrome, Chromium, Firefox and Safari. MIT licensed; see [LICENSE](LICENSE).
