# Thunder Draft Scout

A full-stack draft-prospect comparison and scouting-report tool, built as a
portfolio project for the **OKC Thunder Software Engineer Intern, Basketball
Operations** posting. It's a small end-to-end slice of what that role
describes: a data system that ingests player performance data, evaluates
prospects against it, and surfaces the result through an application a
scout or analyst could actually use.

> **Data note:** the 18 **prospects** are real, named, individually-sourced
> people - see "Data sources" below for a citation on every one. The
> ~150-player **comp pool** that ships by default is still **synthetic**
> (fictional names/stats), because generating it for real requires running
> `backend/data/fetch_live_data.py` from a machine with normal internet
> access (see "Pulling real NBA stats" below) - this sandbox can't reach
> `stats.nba.com`. The app makes this unmistakable at runtime: every player
> card and comp-table row carries a "Real · sourced" / "Live NBA stats" /
> "Synthetic demo" badge, and the header pill shows the live split (e.g.
> "18/18 prospects real · 150 comp-pool (synthetic)"). Run the live fetch
> before presenting this and that pill becomes fully real end to end.

## Why this project, for this role

| Posting asks for... | Where it shows up here |
|---|---|
| Manage/implement/maintain data systems for player evaluation & strategic planning | SQLAlchemy-backed data model (`backend/app/models.py`), a pluggable ingestion layer (synthetic vs. live), and a REST API over it |
| Python, JavaScript, SQL | FastAPI + SQLAlchemy backend (Python/SQL), vanilla JS + Chart.js frontend |
| Front-end / back-end engineering, data engineering, database admin, cloud services | Full FastAPI backend, static JS frontend, SQLite-by-default schema that's a one-line env var away from Postgres, Dockerfile + docker-compose for deployment |
| Support basketball analytics, player evaluation, physical research | A z-score/k-NN player-comp engine, percentile-based scouting reports, and a durability/availability score as a stand-in for physical-performance monitoring |
| Collaborate on real-time, data-driven decision-making tools | A working API + dashboard a scout could query live while evaluating a prospect |
| Working with & protecting confidential information | See "Handling confidential information" below |

## Architecture

```
thunder-draft-scout/
├── backend/
│   ├── app/
│   │   ├── main.py         FastAPI app & REST endpoints
│   │   ├── models.py       SQLAlchemy ORM (single Player table: pros + prospects)
│   │   ├── schemas.py      Pydantic request/response contracts
│   │   ├── similarity.py   z-score / weighted-distance player-comp engine
│   │   ├── scouting.py     percentile ranks, durability score, report text
│   │   └── database.py     SQLite by default; DATABASE_URL env var overrides
│   ├── data/
│   │   ├── generate_seed_data.py   synthetic pro comp-pool generator
│   │   ├── real_prospects.py       the 18 real, individually-sourced prospects
│   │   ├── build_seed.py           combines the two into the shipped seed.csv
│   │   ├── fetch_live_data.py      real stats.nba.com ingestion via nba_api
│   │   └── seed.csv                pre-generated default dataset (committed)
│   └── tests/               pytest: similarity engine, scouting logic, API
├── frontend/                 vanilla HTML/CSS/JS dashboard (Chart.js, vendored)
├── scripts/init_db.py        loads any CSV in the schema into the DB
├── Dockerfile / docker-compose.yml
└── requirements.txt / requirements-live.txt
```

**Data flow:** a CSV (synthetic or live) → `scripts/init_db.py` → SQLite via
SQLAlchemy → FastAPI reads it for every request → the frontend calls the
JSON API and renders it. Nothing is precomputed or cached, so adding a
prospect through the UI is immediately reflected in its scouting report.

### The comp engine, briefly

Prospects and pros share one table and one stat schema. To find comps for a
prospect: pull the pro pool (optionally same-position only, falling back to
the full pool if a position group is too thin), z-score every stat column
against that pool's own mean/std, apply hand-tuned weights (production and
efficiency stats count more than age or raw size), and rank by weighted
Euclidean distance. It's deliberately simple - explainable in a sentence,
no ML dependency beyond `numpy` - because the interesting engineering here
is the pipeline and interface (`prospect + pool -> ranked comps`), which is
exactly what a more sophisticated model would slot into later.

The scouting report is separate and rule-based: percentile rank per stat
vs. positional peers (turnovers inverted, since lower is better), templated
strength/weakness sentences off threshold crossings, and a durability score
standing in for the physical-performance signal a real Basketball Ops
pipeline would get from sports-science data. That score deliberately uses
**two different yardsticks**: an NBA player's score is games played / 82
(a fixed, universal season length), while a *prospect's* score is a
percentile rank of games played against other prospects, not against 82 -
a college season is ~30-40 games and varies by tournament run, so dividing
by 82 would flag a healthy player who played every game as "unavailable"
simply because his season was shorter (this was a real bug caught while
wiring up real prospect data - Aday Mara played all 40 of Michigan's games
and the old formula scored him a misleading 48.8/100).

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/init_db.py     # loads the committed backend/data/seed.csv into SQLite

uvicorn backend.app.main:app --reload
```

`backend/data/seed.csv` is already committed (real prospects + synthetic pro
pool - see the data note above), so this works with zero regeneration. To
rebuild it from source instead (e.g. after editing `real_prospects.py`):

```bash
python backend/data/build_seed.py   # regenerates backend/data/seed.csv
python scripts/init_db.py
```

Open http://127.0.0.1:8000 - the API is also mounted there (e.g.
http://127.0.0.1:8000/docs for interactive OpenAPI docs).

### With Docker

```bash
docker compose up --build
```

### Pulling real NBA stats instead of synthetic data

```bash
pip install -r requirements-live.txt
python backend/data/fetch_live_data.py --season 2024-25
python scripts/init_db.py --csv backend/data/seed_live.csv
```

Run this from a machine with normal internet access - `stats.nba.com`
blocks most cloud/data-center IP ranges, so it won't work from CI or a
locked-down sandbox. There's no public API for un-drafted college
prospects, so those still get added by hand through the "+ Add" button or
`POST /api/prospects`.

## Data sources

Every prospect row's `source_note` field (visible in the UI under the
player's name) cites where it came from; this is the same list, for a
quick audit. Pulled September 2026 - college stats and draft outcomes are
final/historical (won't change), but re-verify anything with a "2027"
season tag since those players' actual seasons hadn't started yet.

**2026 draftees (real final college-season stats + real combine
measurables):**

| Player | School | Drafted by | Sources |
|---|---|---|---|
| AJ Dybantsa | BYU | Washington Wizards (No. 1) | Wikipedia; 2026 NBA Draft Combine |
| Darryn Peterson | Kansas | Utah Jazz (No. 2) | Wikipedia; 2026 NBA Draft Combine |
| Cameron Boozer | Duke | Memphis Grizzlies (No. 3) | Tankathon 2026 Draft profile |
| Caleb Wilson | North Carolina | Chicago Bulls (No. 4) | Tankathon 2026 Draft profile |
| Aday Mara | Michigan | **Oklahoma City Thunder (No. 12)** | Wikipedia; 2026 NBA Draft Combine |
| Yaxel Lendeborg | Michigan | Golden State Warriors (No. 11) | Tankathon 2026 Draft profile |
| Nate Ament | Tennessee | Miami Heat / traded to Milwaukee (No. 13) | Tankathon 2026 Draft profile |
| Jayden Quaintance | Kentucky | San Antonio Spurs (No. 20) | Tankathon 2026 Draft profile |

**2027 board (real recruits, bio-only - no college stat line exists yet,
so none is invented):**

Tyran Stokes, Caleb Holt, Jordan Smith Jr., Bruce Branch III, Anthony
Thompson, Cameron Williams, Baba Oladotun, Brandon McCoy Jr., Braylon
Mullins, Patrick Ngongba II - all via the Tankathon 2027 NBA Draft Big
Board.

Adding more real prospects yourself: edit `backend/data/real_prospects.py`
(each entry documents its own source inline) and re-run
`python backend/data/build_seed.py && python scripts/init_db.py`, or use
the "+ Add" button in the UI, which now has a Source field - anything
entered there is labeled "Real · sourced" in the app; anything left blank
is labeled as an unsourced manual entry, not "real."

### Tests

```bash
pip install -r requirements.txt   # includes pytest
pytest
```

21 tests cover the similarity engine (position filtering, fallback
behavior, missing-stat handling, self-exclusion), the scouting/percentile
logic (inverted turnover scoring, the pro-vs-prospect durability split
described above), and the API (validation, 404s, create → report
round-trip).

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/players?position=PG` | list the pro comp pool, optionally filtered |
| GET | `/api/prospects` | list draft prospects |
| POST | `/api/prospects` | add a prospect |
| GET | `/api/prospects/{id}/report` | full scouting report: percentiles, comps, durability, summary |

## Handling confidential information

The posting specifically calls out "experience working with and protecting
confidential information" - real basketball-ops data (medical records,
contract details, scouting notes) is sensitive, so a few things worth
calling out even in a demo project:

- The `injury_notes` / `scout_notes` fields are deliberately free text, not
  structured medical data - this project stores availability (games played)
  as the durability signal, not health records.
- CORS is wide open (`allow_origins=["*"]`) for local demo convenience; a
  real deployment would restrict it to the actual frontend origin and add
  auth (this project has none - anyone who can reach the API can read/write
  everything).
- `DATABASE_URL` is read from an environment variable rather than hardcoded,
  so credentials for a real deployment never need to touch source control.
- Pydantic schemas validate every write (e.g. `position` is constrained to
  the five valid codes), which is the first line of defense against bad or
  malicious input reaching the database.

None of this is production-grade security - it's meant to show awareness of
the problem in a project scoped for an internship application, not to be a
HIPAA-compliant system.

## Possible next steps

- Run `fetch_live_data.py` on a normal internet connection and reload -
  turns the comp pool from synthetic to real, end to end.
- Expand `real_prospects.py` beyond 18 entries as the 2026-27 college
  season plays out and real stat lines exist for more 2027 board prospects.
- Swap the hand-weighted similarity engine for a learned embedding (e.g.
  trained on tracking data) while keeping the same `prospect + pool ->
  comps` interface.
- Blend the durability score with real workload/travel data instead of just
  games played.
- Add auth + audit logging before pointing this at anything real.
- Deploy the container to a cloud provider (Render/Fly.io/AWS) with a
  managed Postgres instance instead of SQLite.
