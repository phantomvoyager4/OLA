# Shared base: dependencies only, so a code change never reinstalls them.
FROM python:3.12-slim AS base

WORKDIR /app

COPY src/BACKEND/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# --- Development -----------------------------------------------------------
# No COPY of the source: docker-compose bind-mounts ./src over /app/src so edits
# on the host are visible immediately, and uvicorn restarts the worker itself.
# watchfiles replaces uvicorn's fallback stat-polling reloader, which rescans
# every file on an interval and is noticeably slower on a mounted volume.
FROM base AS dev

RUN pip install --no-cache-dir watchfiles==1.2.0

CMD ["uvicorn", "BACKEND.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--reload-dir", "/app/src"]

# --- Production ------------------------------------------------------------
# Last stage, so a plain `docker build` still produces the deployable image.
FROM base AS prod

COPY src/ /app/src/

CMD ["uvicorn", "BACKEND.main:app", "--host", "0.0.0.0", "--port", "8000"]
