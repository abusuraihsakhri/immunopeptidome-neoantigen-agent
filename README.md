# Immunopeptidome Neoantigen Agent

> **Domain:** Computational Biology & AI Drug Discovery
> **Reference Guidelines & Standards:** `wwPDB, IUPAC & CLSI Computational Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Immunopeptidome Neoantigen Agent** is an advanced analytical and computational platform implementing NetMHCpan HLA-I/II peptide binding affinity (%Rank, IC50 nM) neoantigen predictor.

The system provides a multi-worker evaluation engine that processes task payloads through specialized workers, generates consensus dossiers, and maintains a tamper-evident HMAC-SHA256 audit trail.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Multi-Worker Architecture**: Specialized workers for QC, safety escalation, and protocol conformance.
- **Enrichment Engines**: Tumor board preparation, dose calculation, treatment response assessment, and more.

---

## 🚀 Quick Start

### Installation

```bash
pip install -e .
```

### Dependencies

- Python >= 3.9
- FastAPI & uvicorn (for REST API server)
- Pydantic v2

---

## 💻 CLI Usage

### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task/case identifier
- `--target`: Target entity or genomic identifier
- `--primary`: Primary domain measurement or score (float)
- `--secondary`: Secondary kinetic or confidence score (float)
- `--critical`: Flag for emergency escalation (boolean)
- `--status`: Status code or phenotype descriptor

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Parameter / observation metric | Required |
| `target_identifier` | Parameter / observation metric | Required |
| `primary_metric` | Parameter / observation metric | Required |
| `secondary_metric` | Parameter / observation metric | Required |
| `is_critical_flag` | Boolean critical flag | Required |
| `status_descriptor` | Status or phenotype descriptor | Required |

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Operational metrics |
| POST | `/api/audit` | Process task evaluation |
| POST | `/api/chat` | Query supervisor chat |
| GET | `/api/audit/logs` | Retrieve audit trail |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC signing key for audit trail | Random (ephemeral) |
| `MODEL_PROVIDER` | LLM provider selection | `mock` |

> **Security Note:** For production deployments, always set `AUDIT_SECRET_KEY` environment variable. Without it, a random key is generated at startup, which means audit trail integrity cannot be verified across restarts.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t immunopeptidome-neoantigen-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key immunopeptidome-neoantigen-agent
```

Or using Docker Compose:

```bash
# Set your audit key
export AUDIT_SECRET_KEY=your-production-key

# Launch
docker-compose up -d
```

---

## 📁 Project Structure

```
immunopeptidome-neoantigen-agent/
├── agents/                  # Core agent framework
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Multi-worker orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics
│   └── streamer.py         # WebSocket telemetry
├── neoantigen_predictor/    # Domain-specific prediction engine
│   ├── agents.py           # Neoantigen-specific agents
│   ├── engine.py           # Core algorithmic engine
│   ├── models.py           # Domain data models
│   ├── cli.py              # Domain CLI
│   └── server.py           # Domain REST server
├── tests/                   # Test suite
├── cli.py                   # Main CLI entry point
├── simulator.py             # High-throughput simulation
├── enrichment.py            # Enrichment feature engines
├── web/index.html           # Operations console UI
├── Dockerfile               # Container definition
├── docker-compose.yml       # Compose configuration
└── pyproject.toml           # Project metadata
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
