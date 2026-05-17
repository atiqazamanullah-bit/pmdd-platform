# Developer Onboarding Guide

Welcome to the PMDD development team! Follow these instructions to set up the system locally.

## Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- `uv` package manager (or pip)

## Environment Setup
1. Copy `.env.example` to `.env`.
2. Add your `OPENAI_API_KEY` and `PINECONE_API_KEY` to the `.env` file.
3. Keep `DATABASE_URL` pointing to localhost if using Docker for the database.

## Running the System Locally

### 1. Start the Database Infrastructure
```bash
docker-compose up -d
```
This spins up PostgreSQL and Redis.

### 2. Setup the Backend
Navigate to the root directory and run the Makefile install command (or use uv directly):
```bash
make install
```
Start the FastAPI server:
```bash
make run
```
The API will be available at `http://localhost:8000/api/v1`.
Check health at `http://localhost:8000/health`.

### 3. Setup the Frontend
Open a new terminal window and navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```
The Next.js dashboard will be available at `http://localhost:3000`.

## Development Guidelines
- **Typing:** All Python code must be strictly typed using standard type hints and Pydantic.
- **Formatting:** We use Ruff for linting and Black for formatting.
- **Commits:** Follow conventional commit messages.
