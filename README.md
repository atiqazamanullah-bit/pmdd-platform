# Pragmatic Meaning Drift Detector (PMDD) 🔬

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

PMDD is a production-grade, multi-agent computational linguistics platform designed to detect pragmatic and semantic drift in large textual corpora.

It utilizes an **Observe-Analyze-Reflect-Validate** cognitive loop powered by LangGraph, ensuring that LLM-driven linguistic interpretations are explicitly grounded in corpus evidence, immune to hallucination, and statistically reliable.

## Features
- **Adaptive Cognitive Agents**: Specialized agents for Pragmatic, Semantic, and Quantitative analysis.
- **Scientific Validation Engine**: Deterministic exact-quote matching prevents LLM hallucinations.
- **Retrieval Augmented Intelligence (RAG)**: Uses Pinecone to recall past reasoning trajectories and theory success rates.
- **Interactive Dashboard**: Next.js workspace with live agent cognitive traces via WebSockets.
- **Publication-Ready Exports**: Automatically generates DOCX/PDF scientific reports.

## Quickstart (Local Simulation)
```bash
# 1. Setup Environment
copy .env.example .env
# Add OPENAI_API_KEY and PINECONE_API_KEY to .env

# 2. Start Infrastructure
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d

# 3. Run the Minimal Viable Demo
python scripts/run_mvp.py
```

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) and [DEPLOYMENT.md](DEPLOYMENT.md) for enterprise deployment strategies.
