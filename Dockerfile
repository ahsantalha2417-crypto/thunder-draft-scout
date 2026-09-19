# Single-container image: FastAPI serves both the JSON API and the static
# frontend, so this is the whole app.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/
COPY scripts/ scripts/

# Bake the synthetic demo dataset into the image so the container is
# immediately useful with zero setup. Mount a volume at /app/backend/data
# (see docker-compose.yml) if you want the DB to persist across restarts,
# or swap it for a live-fetched CSV before building.
RUN python backend/data/generate_seed_data.py \
    && python scripts/init_db.py

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
