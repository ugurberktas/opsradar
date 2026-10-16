"""Simulation endpoint: generates synthetic incidents on demand."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, parsers, redact, simulation as sim_mod
from app.detectors import detect_and_correlate
from app.schemas import SimulationResponse

router = APIRouter(tags=["simulation"])


@router.post("/simulate", response_model=SimulationResponse)
def simulate(seed: int = 42, total_events: int = 60, db: Session = Depends(get_db)):
    """Generate new synthetic events and run detection against them."""
    events = sim_mod.generate_events(seed=seed, total_events=total_events)
    normalized = [parsers.normalize_event(e) for e in events]

    service_cache: dict = {}
    inserted = 0
    for ev in normalized:
        ev["message"] = redact.redact_text(ev["message"])
        ev["raw"] = redact.redact_text(ev.get("raw") or "")
        key = (ev["service"], ev["environment"])
        svc = service_cache.get(key)
        if svc is None:
            svc = (
                db.query(models.Service)
                .filter(models.Service.name == ev["service"])
                .filter(models.Service.environment == ev["environment"])
                .first()
            )
            if svc is None:
                svc = models.Service(
                    name=ev["service"], environment=ev["environment"], status="healthy"
                )
                db.add(svc)
                db.flush()
            service_cache[key] = svc
        le = models.LogEvent(
            service_id=svc.id,
            service=ev["service"],
            environment=ev["environment"],
            timestamp=ev["timestamp"],
            level=ev["level"],
            message=ev["message"],
            raw=ev["raw"],
            redacted=True,
        )
        db.add(le)
        inserted += 1

    db.flush()
    result = detect_and_correlate(db, normalized)
    db.commit()

    return SimulationResponse(
        events_generated=inserted,
        incidents_detected=len(result.incidents),
        scenario="simulated",
    )
