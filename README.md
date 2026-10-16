# OpsRadar — SRE Incident & Log Intelligence Platform

A production-style, local-first web platform that helps DevOps and SRE engineers
detect, investigate, correlate, and manage infrastructure incidents from
application logs. No real Kubernetes cluster, Jenkins, or production access is
required — everything runs on realistic synthetic data.

> **Built for autonomous evaluation:** a single-prompt, full-stack TypeScript +
> Python application with backend API, React frontend, SQLite persistence, rule-
> based incident detection, simulation, tests, and Docker deployment.

---

## 🏗️ Architecture

```
opsradar/
├── backend/                 # Python + FastAPI (+ SQLAlchemy + SQLite)
│   ├── app/
│   │   ├── main.py          # App factory, lifespan, auto-seeding
│   │   ├── database.py      # SQLAlchemy engine/session
│   │   ├── models.py        # Service, LogEvent, Incident, IncidentEvent
│   │   ├── schemas.py       # Pydantic v2 request/response schemas
│   │   ├── redact.py        # Sensitive-data redaction (passwords, tokens, JWT)
│   │   ├── parsers.py       # JSONL parsing + normalization
│   │   ├── detectors.py     # Rule-based detection & correlation engine
│   │   ├── simulation.py    # Reproducible synthetic log generator
│   │   ├── ai_interface.py  # Optional, disabled-by-default AI provider iface
│   │   └── api/             # REST routers (services, logs, incidents, dashboard, simulation)
│   ├── tests/               # Pytest suite (parsing, redaction, detection, lifecycle, API)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React + TypeScript + Vite + Tailwind + Recharts
│   ├── src/
│   │   ├── lib/api.ts       # Axos API client
│   │   ├── lib/store.ts     # React context state + data fetching
│   │   ├── lib/utils.ts     # Formatters / severity colours
│   │   ├── components/      # UI primitives + charts (ErrorTrend, SeverityDonut, ServiceHealth)
│   │   ├── pages/           # Dashboard, LogsExplorer, Incidents, IncidentDetail, Services
│   │   ├── App.tsx          # Routing (react-router-dom)
│   │   └── tests/           # Vitest suite
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml       # One-command full stack
├── Makefile                 # Convenience targets
└── .env.example
```

### Design decisions
- **Local-first**: SQLite file database; no external services required.
- **Deterministic detection**: rule-based engine (regex signatures, time-window
  correlation, severity assignment). Root causes are labeled `speculative` /
  `likely` and never presented as confirmed fact.
- **Sensitive-data redaction**: passwords, tokens, API keys, Bearer auth headers
  and JWTs are redacted **before** storage and display. No real credentials are
  ever persisted.
- **Reproducible simulation**: fixed random seed (`42`) generates identical demo
  data every run; a "Simulate Incident" button creates new events through the
  backend and mutates state.
- **Separation of concerns**: frontend and backend are cleanly separated, type-
  safe (TypeScript strict + Pydantic), with structured logging via stdlib.

---

## 🚀 Quick Start

### Option A: Docker Compose (recommended)

```bash
cd opsradar
docker compose up --build
```

Then open: **http://localhost:5173** (frontend) — the backend API is at
**http://localhost:8000**.

### Option B: Manual (no Docker)

Backend:
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Frontend (new terminal):
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to backend
```

### One-command test run

```bash
make backend-test   # pytest (backend)
make frontend-test  # vitest (frontend)
```

---

## 📦 What works (verified)

| Acceptance criterion | Status |
|---|---|
| Backend starts successfully | ✅ `uvicorn app.main:app` |
| Frontend starts successfully | ✅ `vite` dev server + production build |
| Database initializes automatically | ✅ SQLAlchemy `create_all` on lifespan |
| Sample data generated | ✅ 200 synthetic events, 6 services, auto-seeded on startup |
| Dashboard displays real backend data | ✅ `/api/dashboard` returns live stats |
| Incident detection produces results | ✅ JDBC, Redis, CrashLoopBackOff, HTTP 5xx, OOM, timeouts |
| Simulation changes application state | ✅ `/api/simulate` inserts events + runs detection |
| Ack/resolve persist | ✅ SQLite, status transitions tested |
| Automated tests pass | ✅ 23 backend + 7 frontend tests |
| Docker Compose valid | ✅ `docker compose up --build` |

---

## 🔌 API Overview

Base path: `/api`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/services` | GET | List monitored services with log/incident counts |
| `/dashboard` | GET | Aggregated stats: counts, severity/status distribution, error trend, service health, recent events |
| `/logs` | GET | List/filter log events (`?service=`, `?level=`, `?search=`, `?limit=`) |
| `/logs/ingest` | POST | Ingest parsed log event objects (`{ events: [...] }`) |
| `/logs/ingest/file` | POST | Upload a JSONL log file (`multipart/form-data`) |
| `/incidents` | GET | List incidents (`?status=`, `?severity=`, `?service=`) |
| `/incidents/{id}` | GET | Single incident detail |
| `/incidents/{id}` | PATCH | Acknowledge/resolve (`{ "status": "acknowledged\|resolved" }`) |
| `/simulate` | POST | Generate synthetic incidents (`?seed=`, `?total_events=`) |

Example:
```bash
curl http://localhost:8000/api/dashboard
curl http://localhost:8000/api/incidents?severity=CRITICAL
curl -X POST http://localhost:8000/api/simulate?seed=99&total_events=50
```

---

## 🧪 Detection Scenarios

The rule engine detects and correlates:

1. **Database connection pool exhaustion** — `java.sql.SQLException`, HikariCP pool exhausted, `CommunicationsException`
2. **Repeated JDBC connection errors** — connection refused on DB ports
3. **Redis connectivity problems** — `redis.exceptions.ConnectionError`, `ECONNREFUSED`, `6379`
4. **Kubernetes pod restart loops** — `CrashLoopBackOff`, `OOMKilled`
5. **HTTP 5xx spikes after deployment** — `500/502/503` responses
6. **Connection timeouts** — `Connection timed out`, `ReadTimeout`, `ConnectTimeout`
7. **Out of memory** — `OutOfMemoryError`, `Java heap space`, `Cannot allocate memory`

Each detected incident records: first/last seen, event count, affected service,
confidence score, a speculative root cause (labeled as such), investigation
steps, and remediation actions. Duplicate identical errors are deduplicated by
signature (`rule:service:environment`).

---

## 🔐 Security & Data Safety

- Sensitive values (passwords, tokens, API keys, Bearer JWTs, Authorization
  headers) are redacted to `***REDACTED***` **before** storage and before any
  frontend display.
- No real credentials, API keys, or production data are included or required.
- The optional AI provider interface (`app/ai_interface.py`) is implemented as a
  disabled-by-default stub that returns `None`; no LLM API key or network call
  is wired in the default build.

---

## 🧹 Project hygiene

- `make backend-test` — runs the full pytest suite.
- `make frontend-test` — runs vitest.
- `npm run build` (frontend) — type-checks (`tsc`) and bundles with Vite.
- `docker compose up --build` — full-stack, single-command deployment.
# opsradar
