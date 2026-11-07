from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.routers import captures, proposals, tasks, plans, memory, users
from backend.app.db.supabase_client import supabase_client

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="THOZHI — Multilingual AI-Powered Personal Planning Assistant Backend API"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RFC 7807 Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem_details(),
        headers={"Content-Type": "application/problem+json"}
    )

# Routers
app.include_router(captures.router, prefix=settings.API_V1_STR)
app.include_router(proposals.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(memory.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System"])
async def health_check():
    supabase_status = await supabase_client.check_health()
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": supabase_status,
        "primary_asr": {
            "engine": "Gnani AI Prisma v3",
            "configured": bool(settings.GNANI_API_KEY),
            "endpoint": settings.GNANI_API_URL,
            "model": "prisma-v3.0"
        },
        "failover_asr": {
            "engine": "Sarvam AI Saaras v3",
            "configured": bool(settings.SARVAM_API_KEY)
        },
        "nlu_engine": {
            "configured": bool(settings.GEMINI_API_KEY)
        }
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to THOZHI API. The AI proposes. The user decides.",
        "docs_url": "/docs",
        "health_url": "/health"
    }
