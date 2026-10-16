"""Simulation endpoint: generates synthetic incidents on demand."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import simulation as sim_mod
from app.database import get_db
from app.ingestion import ingest_events
from app.schemas import SimulationResponse

router = APIRouter(tags=["simulation"])


@router.post("/simulate", response_model=SimulationResponse)
def simulate(
    seed: int = Query(default=42, ge=0, le=2_147_483_647),
    total_events: int = Query(default=60, ge=1, le=1_000),
    db: Session = Depends(get_db),
):
    """Generate new synthetic events and run detection against them."""
    events = sim_mod.generate_events(seed=seed, total_events=total_events)
    try:
        result = ingest_events(db, events)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return SimulationResponse(
        events_generated=result.ingested,
        incidents_detected=result.incidents_created,
        scenario="simulated",
    )
