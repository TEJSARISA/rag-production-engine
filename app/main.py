from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Depends, Security
from app.api.v1.api import api_router
from app.core import config
from app.core.security import verify_api_key
from app.db.base import Base
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables & pgvector extension on startup
    async with engine.begin() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.run_sync(Base.metadata.create_all)
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="Asynchronous RAG Service",
        version="1.0.0",
        description="Production-grade Async RAG API Service with pgvector, Celery background ingestion & DeepEval evaluation",
        lifespan=lifespan,
    )

    # Protect API v1 endpoints with API Key verification
    app.include_router(
        api_router,
        prefix="/api/v1",
        dependencies=[Security(verify_api_key)]
    )
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=config.settings.DEBUG)
