# PMDD Architecture Documentation

## Overview
The Pragmatic Meaning Drift Detector (PMDD) is an advanced, multi-agent computational linguistics platform. It uses a hybrid Next.js frontend and a FastAPI/LangGraph backend to orchestrate autonomous AI agents analyzing large text corpora for semantic and pragmatic shifts.

## Repository Structure

- `frontend/`: Next.js 14 application (React, Tailwind, Shadcn). Handles corpus upload and dashboard visualization.
- `backend/`: FastAPI application. Exposes async REST endpoints.
- `agents/`: LangChain/LangGraph cognitive agents. Includes:
  - Agent 1: Preprocessor
  - Agent 2: Pragmatic Analyzer
  - Agent 3: Semantic Analyzer
  - Agent 4: Quantitative Analyzer
  - Agent 5: Orchestrator
- `orchestration/`: LangGraph definitions, shared state, and routing logic.
- `memory/`: Episodic memory and Vector RAG implementations (Pinecone).
- `validation/`: Evidence validation and hallucination prevention.
- `reporting/`: PDF and Markdown generation engine for final linguistic analysis.
- `infrastructure/`: Docker, CI/CD, and DevOps configuration.
- `tests/`: Pytest suite for automated QA.
- `docs/`: Technical documentation and developer onboarding.

## Key Technologies
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Asyncpg, LangGraph, OpenAI.
- **Frontend:** TypeScript, Next.js, Tailwind CSS.
- **Databases:** PostgreSQL (Supabase) for structured metadata, Pinecone for vector embeddings.
- **DevOps:** Docker, Poetry, Make.

## Agent Communication Protocol
Agents pass a strictly typed `PMDDState` dictionary (defined in `orchestration/state.py`). Validation hooks intercept agent outputs before state updates to ensure academic rigor and traceability.
