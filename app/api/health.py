"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.api_version,
        "environment": settings.environment,
        "ai_provider": settings.ai_provider,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/container orchestration."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
