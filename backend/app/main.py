"""OpsRadar FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app import simulation as sim_mod
from app.api import services as services_router
from app.api import logs as logs_router
from app.api import incidents as incidents_router
from app.api import dashboard as dashboard_router
from app.api import simulation as simulation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed sample simulation data automatically if DB is empty
    from app.database import SessionLocal
    from app import models, parsers
    from app.detectors import detect_and_correlate

    db = SessionLocal()
    try:
        if db.query(models.Service).count() == 0:
            events = sim_mod.generate_events(seed=42, total_events=200)
            normalized = [parsers.normalize_event(e) for e in events]
            from app import redact

            for ev in normalized:
                ev["message"] = redact.redact_text(ev["message"])
                ev["raw"] = redact.redact_text(ev.get("raw") or "")

            # upsert services
            service_names = sorted({e["service"] for e in normalized})
            service_objs = {}
            for name in service_names:
                env = next(e["environment"] for e in normalized if e["service"] == name)
                svc = models.Service(name=name, environment=env, status="healthy")
                db.add(svc)
                service_objs[name] = svc
            db.flush()

            for ev in normalized:
                svc = service_objs.get(ev["service"])
                le = models.LogEvent(
                    service_id=svc.id if svc else None,
                    service=ev["service"],
                    environment=ev["environment"],
                    timestamp=ev["timestamp"],
                    level=ev["level"],
                    message=ev["message"],
                    raw=ev["raw"],
                    redacted=True,
                )
                db.add(le)
            db.flush()
            detect_and_correlate(db, normalized)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="OpsRadar — SRE Incident & Log Intelligence",
    description="Local-first incident detection from application logs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services_router.router, prefix="/api")
app.include_router(logs_router.router, prefix="/api")
app.include_router(incidents_router.router, prefix="/api")
app.include_router(dashboard_router.router, prefix="/api")
app.include_router(simulation_router.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
