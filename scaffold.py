import os

dirs = [
    "backend/api/routes",
    "backend/core",
    "backend/db/models",
    "backend/services",
    "agents",
    "orchestration",
    "memory",
    "rag",
    "validation",
    "reporting",
    "infrastructure",
    "tests/backend",
    "tests/agents",
    "docs"
]

files = {
    "backend/__init__.py": "",
    "backend/api/__init__.py": "",
    "backend/api/routes/__init__.py": "",
    "backend/core/__init__.py": "",
    "backend/db/__init__.py": "",
    "backend/db/models/__init__.py": "",
    "agents/__init__.py": "",
    "orchestration/__init__.py": "",
    "memory/__init__.py": "",
    "rag/__init__.py": "",
    "validation/__init__.py": "",
    "reporting/__init__.py": "",
    "tests/__init__.py": "",
    
    "backend/main.py": """from fastapi import FastAPI
from backend.core.config import settings
from backend.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PMDD Agentic Linguistic Analyzer API"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
""",

    "backend/core/config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PMDD Research API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pmdd"
    OPENAI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
""",

    "backend/api/routes/router.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to PMDD API"}
""",

    "backend/api/routes/__init__.py": """from .router import router
""",

    "backend/core/logging.py": """import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("pmdd")

logger = setup_logging()
""",

    "backend/db/base.py": """from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
""",

    "backend/db/models/corpus.py": """from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.db.base import Base

class Corpus(Base):
    __tablename__ = "corpora"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    token_count = Column(Integer)
    s3_uri = Column(String)
""",

    "orchestration/state.py": """from typing import TypedDict, List, Dict, Any

class PMDDState(TypedDict):
    corpus_id: str
    segment_id: str
    raw_text: str
    agent_outputs: Dict[str, Any]
    validation_status: str
    retry_count: int
    final_report_uri: str
""",

    "agents/base.py": """from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    @abstractmethod
    async def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def reflect(self, output: Dict[str, Any]) -> float:
        pass
""",

    "memory/episodic.py": """class EpisodicMemoryManager:
    def __init__(self):
        pass
        
    async def log_episode(self, agent_id: str, payload: dict):
        # TODO: Store to Pinecone / Supabase
        pass
        
    async def retrieve_similar(self, context: dict):
        return []
""",

    "validation/hooks.py": """def check_hallucination(corpus_text: str, quoted_evidence: str) -> bool:
    \"\"\"Returns True if evidence is verified in corpus.\"\"\"
    return quoted_evidence in corpus_text
""",

    "pyproject.toml": """[tool.poetry]
name = "pmdd-core"
version = "0.1.0"
description = "Pragmatic Meaning Drift Detector"
authors = ["GC"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = "^0.29.0"
pydantic-settings = "^2.2.1"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.29"}
asyncpg = "^0.29.0"
alembic = "^1.13.1"
openai = "^1.14.2"
langchain = "^0.1.13"
langgraph = "^0.0.30"
pinecone-client = "^3.2.2"

[tool.ruff]
line-length = 88
target-version = "py311"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",

    "requirements.txt": """fastapi==0.110.0
uvicorn==0.29.0
pydantic-settings==2.2.1
sqlalchemy[asyncio]==2.0.29
asyncpg==0.29.0
alembic==1.13.1
openai==1.14.2
langchain==0.1.13
langgraph==0.0.30
pinecone-client==3.2.2
""",

    ".env.example": """PROJECT_NAME="PMDD Research API"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pmdd"
OPENAI_API_KEY="sk-..."
PINECONE_API_KEY="..."
""",

    "docker-compose.yml": """version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: pmdd
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
""",

    "Makefile": """install:
\tuv pip install -r requirements.txt

run:
\tuvicorn backend.main:app --reload --port 8000

test:
\tpytest tests/
"""
}

def scaffold():
    # Create dirs
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Create files
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Scaffolding complete.")

if __name__ == "__main__":
    scaffold()
