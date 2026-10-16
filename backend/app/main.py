"""OpsRadar FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import simulation as sim_mod
from app.api import dashboard as dashboard_router
from app.api import incidents as incidents_router
from app.api import logs as logs_router
from app.api import services as services_router
from app.api import simulation as simulation_router
from app.database import init_db
from app.ingestion import ingest_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed sample simulation data automatically if DB is empty
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_demo = os.getenv("OPSRADAR_SEED_DEMO", "true").lower() in {"1", "true", "yes"}
        if seed_demo and db.query(models.Service).count() == 0:
            events = sim_mod.generate_events(seed=42, total_events=200)
            ingest_events(db, events)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    yield


app = FastAPI(
    title="OpsRadar — SRE Incident & Log Intelligence",
    description="Local-first incident detection from application logs.",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "OPSRADAR_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)

app.include_router(services_router.router, prefix="/api")
app.include_router(logs_router.router, prefix="/api")
app.include_router(incidents_router.router, prefix="/api")
app.include_router(dashboard_router.router, prefix="/api")
app.include_router(simulation_router.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
