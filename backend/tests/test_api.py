import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from tests.conftest import make_pro, make_prospect  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "api_test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # seed a minimal pool + one prospect directly through the same session factory
    session = TestingSessionLocal()
    session.add_all(
        [
            make_pro("Vet Guard A", "PG", ast_pg=7, pts_pg=16),
            make_pro("Vet Guard B", "PG", ast_pg=5, pts_pg=20),
            make_pro("Vet Guard C", "PG", ast_pg=9, pts_pg=12),
            make_prospect("Rookie Guard", "PG", ast_pg=6, pts_pg=15),
        ]
    )
    session.commit()
    session.close()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_players_excludes_prospects(client):
    r = client.get("/api/players")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()}
    assert "Rookie Guard" not in names
    assert "Vet Guard A" in names


def test_list_prospects(client):
    r = client.get("/api/prospects")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()}
    assert names == {"Rookie Guard"}


def test_create_prospect_validates_position(client):
    r = client.post("/api/prospects", json={"name": "Bad Position", "position": "ZZ"})
    assert r.status_code == 422


def test_create_and_report_roundtrip(client):
    created = client.post(
        "/api/prospects",
        json={"name": "New Prospect", "position": "PG", "pts_pg": 14, "ast_pg": 6, "games_played": 30},
    )
    assert created.status_code == 201
    prospect_id = created.json()["id"]

    report = client.get(f"/api/prospects/{prospect_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["prospect"]["name"] == "New Prospect"
    assert "summary" in body and body["summary"]
    assert len(body["comparables"]) > 0


def test_report_404_for_unknown_prospect(client):
    r = client.get("/api/prospects/999999/report")
    assert r.status_code == 404
