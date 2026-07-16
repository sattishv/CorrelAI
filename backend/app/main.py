"""
------------------------------------------------------------------------------
CorrelAI

Main Application Entry Point

This module creates and configures the FastAPI application.

------------------------------------------------------------------------------
"""

from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import logger


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Application startup hook.
    """
    logger.info("Starting CorrelAI backend...")


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint for basic application information.
    """
    return {
        "application": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "UP"}