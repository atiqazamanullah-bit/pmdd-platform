from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PMDD Research API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Use SQLite by default for local dev to avoid needing a running Postgres instance
    DATABASE_URL: str = "sqlite+aiosqlite:///./pmdd.db"
    
    OPENAI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Dev secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    class Config:
        env_file = ".env"

settings = Settings()
