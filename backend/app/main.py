"""
Thunder Draft Scout - FastAPI backend.

Endpoints:
  GET  /api/players                 list pro comp-pool players (filter by position)
  GET  /api/prospects                list draft prospects
  POST /api/prospects                add a new prospect
  GET  /api/prospects/{id}/report    full scouting report: percentiles, comps, summary
  GET  /api/health                   liveness check (handy for container/cloud health probes)

Serves the static frontend from /frontend as well, so `uvicorn app.main:app`
is the only command needed to run the whole thing.
"""
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas, scouting, similarity
from .database import Base, SessionLocal, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Thunder Draft Scout API",
    description="Draft prospect comparison & scouting-report tool built for the "
    "OKC Thunder Basketball Operations Software Engineer Intern application.",
    version="0.1.0",
)

# Permissive CORS is fine for a local portfolio project; a real deployment
# would restrict this to the frontend's actual origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/players", response_model=list[schemas.PlayerOut])
def list_players(position: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Player).filter(models.Player.is_prospect.is_(False))
    if position:
        query = query.filter(models.Player.position == position.upper())
    return query.order_by(models.Player.name).all()


@app.get("/api/prospects", response_model=list[schemas.PlayerOut])
def list_prospects(db: Session = Depends(get_db)):
    return (
        db.query(models.Player)
        .filter(models.Player.is_prospect.is_(True))
        .order_by(models.Player.name)
        .all()
    )


@app.post("/api/prospects", response_model=schemas.PlayerOut, status_code=201)
def create_prospect(payload: schemas.ProspectCreate, db: Session = Depends(get_db)):
    # If the submitter cited a source, trust that this is a real person and
    # label it accordingly (surfaced in the UI's data-provenance badge);
    # otherwise it's an unsourced manual entry - still real in intent, but
    # nothing here has verified it, so it isn't labeled "real".
    data_source = "real" if (payload.source_note and payload.source_note.strip()) else "user_entered"
    prospect = models.Player(**payload.model_dump(), is_prospect=True, data_source=data_source)
    db.add(prospect)
    db.commit()
    db.refresh(prospect)
    return prospect


@app.get("/api/prospects/{prospect_id}/report", response_model=schemas.ScoutingReport)
def get_scouting_report(prospect_id: int, db: Session = Depends(get_db)):
    prospect = (
        db.query(models.Player)
        .filter(models.Player.id == prospect_id, models.Player.is_prospect.is_(True))
        .first()
    )
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect not found")

    pool = db.query(models.Player).filter(models.Player.is_prospect.is_(False)).all()
    position_pool = [p for p in pool if p.position == prospect.position]
    if len(position_pool) < 3:
        position_pool = pool  # thin position group -> fall back to full pool

    # Durability compares a prospect's games played against OTHER PROSPECTS,
    # not the pro pool - see scouting.durability_score for why (college and
    # NBA season lengths aren't comparable).
    all_prospects = db.query(models.Player).filter(models.Player.is_prospect.is_(True)).all()
    prospect_peers = [p for p in all_prospects if p.position == prospect.position]
    if len(prospect_peers) < 3:
        prospect_peers = all_prospects

    report = scouting.build_scouting_report(prospect, position_pool, prospect_peers)
    comps = similarity.find_comps(prospect, pool, top_n=5)

    return schemas.ScoutingReport(
        prospect=prospect,
        durability_score=report["durability_score"],
        percentiles=report["percentiles"],
        strengths=report["strengths"],
        weaknesses=report["weaknesses"],
        summary=report["summary"],
        comparables=[
            schemas.ComparablePlayer(player=c.player, similarity_pct=c.similarity_pct) for c in comps
        ],
    )


# --- Static frontend -------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
