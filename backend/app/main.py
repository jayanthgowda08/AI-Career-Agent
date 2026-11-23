"""
main.py — FastAPI Application Entry Point

This is where the FastAPI app is created, middleware is configured,
and all API routers are registered.

Run the server with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import engine, Base, check_database_connection, init_db

# Import API routers
from app.api import auth, profiles, resumes, jobs, search, recommendations, agent, rag, evaluations


# ============================================================
# Lifespan — startup and shutdown logic
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before 'yield' runs at startup.
    Code after 'yield' runs at shutdown.
    """
    # --- Startup ---
    logger.info(f"🚀 Starting {settings.app_name} in {settings.environment} mode...")

    # Ensure uploads directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"📁 Upload directory ready: {settings.upload_dir}")

    # Offload database table initialization & seeding to background thread
    # so Uvicorn binds port 10000 immediately without hitting Render's port scan timeout
    def _background_init_and_seed():
        try:
            init_db()
        except Exception as db_err:
            logger.error(f"⚠️ Database initialization error: {db_err}")

        try:
            from app.database import SessionLocal
            from app.models.job import Job
            from app.services.job_service import seed_jobs_from_file

            with SessionLocal() as db:
                count = db.query(Job).count()
                if count == 0:
                    logger.info("🌱 Database has 0 jobs. Auto-seeding 15 sample jobs...")
                    created, _ = seed_jobs_from_file(db)
                    logger.info(f"✅ Auto-seed complete: {created} jobs created.")
        except Exception as seed_err:
            logger.warning(f"Background auto-seed note: {seed_err}")

    import threading
    threading.Thread(target=_background_init_and_seed, daemon=True).start()

    logger.info("✅ Application startup complete.")
    logger.info(f"📖 API docs available at: http://localhost:8000/docs")

    yield  # App runs here

    # --- Shutdown ---
    logger.info("🛑 Application shutting down...")


# ============================================================
# FastAPI App Instance
# ============================================================
app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered career assistance platform with semantic job search, "
        "personalised recommendations and an LLM-powered career agent."
    ),
    version="0.1.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc UI
    lifespan=lifespan,
)


# ============================================================
# CORS Middleware
# ============================================================
# Allow all web origins (Netlify, local dev, custom domains) dynamically
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?:\/\/.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Root and Health Endpoints
# ============================================================
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint — confirms the API is running.
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": "0.1.0",
        "build": "deploy-fast-recs-v3",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint — used by Docker and deployment platforms
    to verify the service is alive and the database is reachable.
    """
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "connected" if db_status else "unreachable",
    }


# ============================================================
# API Routers
# ============================================================
app.include_router(auth.router,            prefix="/api/auth",            tags=["Authentication"])
app.include_router(profiles.router,        prefix="/api/profiles",        tags=["Profiles"])
app.include_router(resumes.router,         prefix="/api/resumes",         tags=["Resumes"])
app.include_router(jobs.router,            prefix="/api/jobs",            tags=["Jobs"])
app.include_router(search.router,          prefix="/api/search",          tags=["Semantic Search"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(agent.router,           prefix="/api/agent",           tags=["AI Career Agent"])
app.include_router(rag.router,             prefix="/api/rag",             tags=["RAG Career Guidance"])
app.include_router(evaluations.router,     prefix="/api/evaluations",     tags=["System Evaluations"])


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
