"""
FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Interactive API docs:
    http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown hooks.

    Later we will:
    - connect to the database on startup
    - start the background scheduler
  """
    settings = get_settings()
    print(f"Starting {settings.app_name} ({settings.app_env})...")
    yield
    print(f"Shutting down {settings.app_name}...")


def create_app() -> FastAPI:
    """Application factory — keeps main.py testable and modular."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="API uptime monitoring — track health, response time, and uptime.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS: allows a future frontend (React, etc.) to call this API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint — confirms the API is running."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.

        Load balancers and Docker use this to verify the app is alive.
        We will add a database ping here in Step 2.
        """
        return {"status": "ok", "service": settings.app_name}

    return app


# Uvicorn imports this object: uvicorn app.main:app
app = create_app()
