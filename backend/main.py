from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.routes import router as api_router
from backend.api.routes.websocket import router as ws_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.projects import router as projects_router
from backend.db.database import init_db
import os

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PMDD Agentic Linguistic Analyzer API"
)

@app.on_event("startup")
async def startup_event():
    await init_db()

# Crucial for Next.js to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects")
app.include_router(ws_router, prefix="/ws")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
