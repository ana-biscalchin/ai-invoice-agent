"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health_router, invoice_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AI Invoice Agent...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"AI Provider: {settings.ai_provider}")

    yield

    # Shutdown
    logger.info("Shutting down AI Invoice Agent...")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(invoice_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Invoice Agent",
        "version": settings.api_version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
    }
