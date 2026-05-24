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

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import check_database_connection, engine
from app.workers.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown hooks.

    - Verifies DB on startup
    - Starts background health-check scheduler
    - Disposes connection pool on shutdown
    """
    settings = get_settings()
    print(f"Starting {settings.app_name} ({settings.app_env})...")

    if await check_database_connection():
        print("Database connection: OK")
    else:
        print("WARNING: Database connection failed — check DATABASE_URL in .env")

    start_scheduler()
    print(
        f"Health check scheduler: every {settings.scheduler_tick_seconds}s "
        f"(timeout {settings.health_check_timeout_seconds}s)"
    )

    yield

    stop_scheduler()
    await engine.dispose()
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

    # Versioned API routes (auth, endpoints, dashboard — added step by step)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

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

        Returns 200 if the API process is up.
        `database` is "connected" only when PostgreSQL answers SELECT 1.
        """
        db_ok = await check_database_connection()
        return {
            "status": "ok" if db_ok else "degraded",
            "service": settings.app_name,
            "database": "connected" if db_ok else "disconnected",
        }

    return app


# Uvicorn imports this object: uvicorn app.main:app
app = create_app()
