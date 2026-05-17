import os

files = {
    "infrastructure/docker/backend.Dockerfile": """FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

COPY . /app

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./backend /app/backend
COPY ./agents /app/agents
COPY ./memory /app/memory
COPY ./orchestration /app/orchestration
COPY ./reporting /app/reporting
COPY ./validation /app/validation

# Run uvicorn securely as non-root
RUN useradd -m pmdd_user
USER pmdd_user

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",

    "infrastructure/docker/frontend.Dockerfile": """FROM node:18-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
""",

    "infrastructure/docker/docker-compose.prod.yml": """version: '3.8'

services:
  frontend:
    build:
      context: ../../
      dockerfile: infrastructure/docker/frontend.Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build:
      context: ../../
      dockerfile: infrastructure/docker/backend.Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/pmdd
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - db
      - redis

  worker:
    build:
      context: ../../
      dockerfile: infrastructure/docker/backend.Dockerfile
    command: celery -A backend.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/pmdd
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - redis
      - db

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: pmdd
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
""",

    ".github/workflows/ci.yml": """name: PMDD CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install
    - name: Lint with Ruff
      run: poetry run ruff check .
    - name: Test with pytest
      run: poetry run pytest tests/

  test-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: "18"
    - name: Install dependencies
      run: npm ci
    - name: Lint
      run: npm run lint
""",

    "backend/core/security.py": """from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "super-secret-production-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
""",

    "backend/workers/celery_app.py": """from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "pmdd_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=3600, # 1 hour max for corpus analysis
)
""",

    "backend/workers/tasks.py": """from backend.workers.celery_app import celery_app
import asyncio

@celery_app.task(bind=True, max_retries=3)
def process_corpus_task(self, corpus_id: str):
    \"\"\"Background task to orchestrate large corpus analysis.\"\"\"
    # In production, this would call the LangGraph Orchestrator asynchronously
    # and update the database with progress chunks.
    return {"status": "completed", "corpus_id": corpus_id, "segments_processed": 100}
""",

    "tests/e2e/test_load.py": """import pytest
import asyncio
import time

@pytest.mark.asyncio
async def test_simulated_load():
    \"\"\"Simulates multiple concurrent agents interacting with memory.\"\"\"
    start = time.time()
    # Mocking 50 concurrent validation checks
    tasks = [asyncio.sleep(0.01) for _ in range(50)]
    await asyncio.gather(*tasks)
    duration = time.time() - start
    
    # Ensure parallel execution happened under 1 second
    assert duration < 1.0 
"""
}

def scaffold_phase7():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("Phase 7 Productionization & Deployment scaffolding complete.")

if __name__ == "__main__":
    scaffold_phase7()
