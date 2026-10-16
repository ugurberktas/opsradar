# OpsRadar

OpsRadar is a local-first SRE incident and log intelligence dashboard. It ingests
JSONL application logs, redacts common credentials before persistence, applies a
deterministic rule engine, correlates related events into incidents, and supports
acknowledgment and resolution workflows.

This repository is a portfolio and learning project. It demonstrates practical
full-stack engineering patterns, but it is **not** presented as a deployed
enterprise monitoring product.

## Features

- Searchable log explorer with service and severity filters
- JSON event ingestion and JSONL file upload with a 5 MiB limit
- Rule-based detection for database, Redis, Kubernetes, OOM, HTTP 5xx, and
  timeout symptoms
- Fifteen-minute, service-and-environment-aware event correlation
- Idempotent event ingestion and incident-event linking
- Explicitly labeled potential root causes, confidence, investigation steps,
  and manual remediation suggestions
- Persistent incident acknowledgment and resolution
- Service health derived from active incident severity
- Synthetic, fictional demo data with deterministic scenario selection
- Responsive dark/light monitoring dashboard
- FastAPI OpenAPI documentation, Docker Compose, and automated CI

No paid service or external AI API is required. The optional AI provider
interface is disabled by default; incident detection and suggestions are
rule-based.

## Architecture

```text
Browser
  │
  ▼
React + TypeScript + Vite
  │  /api (Vite proxy locally, Nginx proxy in Docker)
  ▼
FastAPI routers
  │
  ├── ingestion: normalize → redact → deduplicate → persist
  ├── detection: match rules → time-window correlation → incident lifecycle
  └── queries: dashboard, logs, services, incidents
  │
  ▼
SQLAlchemy + SQLite
```

The backend owns normalization, validation, redaction, correlation, and
persistence. The frontend context performs a single bounded initial load and
exposes stable refresh and mutation actions. Route-level code splitting keeps
the initial browser bundle focused.

## Technology stack

| Area | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts |
| Tests | Pytest, Vitest, Testing Library |
| Quality | Ruff, TypeScript strict mode, npm audit, pip-audit |
| Runtime | Docker Compose, Nginx |

## Quick start with Docker

Requirements: Docker Engine with Compose v2.

```bash
git clone <your-repository-url>
cd opsradar
docker compose up --build
```

Open:

- Dashboard: <http://localhost:5173>
- API health: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>

If either port is already in use:

```bash
OPSRADAR_FRONTEND_PORT=15173 OPSRADAR_BACKEND_PORT=18000 docker compose up --build
```

SQLite data is stored in the named `opsradar-data` volume. Stop the stack with
`docker compose down`. That command preserves the volume.

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The backend seeds fictional demo data only when the database is empty. Disable
that behavior with `OPSRADAR_SEED_DEMO=false`.

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite serves <http://localhost:5173> and proxies `/api` to
`http://127.0.0.1:8000`. Leave `VITE_API_BASE` blank for the supplied proxy,
or set it to an explicit backend origin for a custom setup.

Copy [`.env.example`](.env.example) to `.env` only when overrides are needed.
Never commit the resulting file.

## API overview

All application endpoints use the `/api` prefix.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Process health |
| GET | `/api/dashboard` | Aggregated service, incident, event, and trend data |
| GET | `/api/services` | Services with log and incident counts |
| GET | `/api/logs` | Filtered logs; maximum 500 rows |
| POST | `/api/logs/ingest` | Ingest 1–5,000 JSON event objects |
| POST | `/api/logs/ingest/file` | Ingest a JSONL, log, or text file up to 5 MiB |
| GET | `/api/incidents` | Filtered incidents; maximum 500 rows |
| GET | `/api/incidents/{id}` | Incident detail |
| PATCH | `/api/incidents/{id}` | Acknowledge or resolve an incident |
| POST | `/api/simulate` | Generate synthetic events and run detection |

FastAPI provides the complete request/response schema at
<http://localhost:8000/docs> during local development.

Example:

```bash
curl http://localhost:8000/api/dashboard
curl -X POST 'http://localhost:8000/api/simulate?seed=99&total_events=50'
```

## Detection and sample data

Detection is deterministic. Rules match known log symptoms, assign a severity
and confidence value, and group matching events by rule, service, environment,
and a 15-minute window. HTTP 5xx and timeout warnings require repeated evidence
to reduce single-event false positives. Exact duplicate events are skipped.

Potential causes are hypotheses, not verified facts. The UI and API label them
as `speculative` or `likely`; suggested commands are displayed for a human
operator and are never executed automatically.

The simulator uses only fictional service names and synthetic log messages.
The random seed controls scenario selection; timestamps are generated relative
to the time of the run.

## Testing and quality checks

From the repository root:

```bash
make test
make lint
make build
make audit
```

Equivalent direct commands:

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/ruff check app tests
.venv/bin/pip-audit -r requirements-prod.txt

cd ../frontend
npm test
npm run build
npm audit --audit-level=moderate

cd ..
docker compose config
```

GitHub Actions runs backend tests and linting, frontend tests and builds, both
dependency audits, and Docker Compose validation.

## Security and limitations

- Redaction covers common password, token, API-key, Bearer/JWT, cloud-key, and
  URL-embedded credential patterns before storage. Redaction is best-effort and
  must not be treated as a data-loss-prevention boundary.
- Upload suffixes and sizes are restricted; malformed JSONL lines are counted
  as skipped instead of being persisted as incidents.
- CORS defaults to local development origins and can be changed with
  `OPSRADAR_CORS_ORIGINS`.
- SQLite foreign keys and lock timeouts are enabled. SQLite remains appropriate
  for a single-node demo, not a highly concurrent production deployment.
- There is intentionally no authentication, authorization, TLS termination,
  tenant isolation, retention policy, or audit log. Do not expose this demo to
  an untrusted network.
- The rule engine can produce false positives and false negatives. It does not
  replace alert review or incident response judgment.
- No real credentials, private logs, or proprietary infrastructure data belong
  in this repository or demo database.

See [SECURITY.md](SECURITY.md) for reporting guidance and the threat-model
boundary.

## Repository structure

```text
.
├── .github/workflows/ci.yml
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route handlers
│   │   ├── detectors.py     # Rules and time-window correlation
│   │   ├── ingestion.py     # Shared ingestion transaction
│   │   ├── parsers.py       # JSONL parsing and normalization
│   │   ├── redact.py        # Sensitive-value redaction
│   │   ├── models.py        # SQLAlchemy models
│   │   └── main.py          # Application lifecycle and CORS
│   ├── tests/
│   ├── requirements-prod.txt
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── tests/
│   └── nginx.conf
├── docker-compose.yml
└── Makefile
```

## Screenshots

The dashboard has been verified in mobile and desktop browser viewports. No
image is referenced here until a stable repository screenshot is committed.
To add one, run the Docker stack, capture the real dashboard at a desktop
viewport, store it under `docs/screenshots/`, and then link that file from this
section. Avoid mockups or screenshots containing real operational data.

## Future improvements

- Database migrations and PostgreSQL support
- Cursor pagination for large log volumes
- Structured rule configuration and operator-defined rules
- Incident-event timeline payloads and richer drill-down views
- Authentication and an append-only audit log for multi-user deployments
- Retention controls, export, and OpenTelemetry ingestion
- Browser-level end-to-end tests in CI

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.

OpsRadar is available under the [MIT License](LICENSE).
