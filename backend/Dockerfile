FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so code edits do not invalidate the layer.
#
# The PostgreSQL driver is included because this image is also used by
# `docker compose --profile postgres` and by hosts such as Render that build
# straight from the Dockerfile. Without it, any deployment that sets
# DATABASE_URL to a PostgreSQL URL fails at import time with
# "No module named 'psycopg'".
COPY requirements.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-postgres.txt

COPY . .

# The SQLite database and export artefacts live here; mount a volume in
# docker-compose so they survive container rebuilds.
RUN mkdir -p /app/data/raw /app/data/cleaned /app/data/exports /app/data/demo

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
