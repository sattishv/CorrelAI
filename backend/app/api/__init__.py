"""
------------------------------------------------------------------------------
CorrelAI

API Package

Exports the FastAPI router and API schemas.

------------------------------------------------------------------------------
"""

from app.api.router import api_router
from app.api.schemas import (
    APIMessage,
    AnalyzeRequest,
    AnalyzeSummaryResponse,
    ArtifactUploadResponse,
    ErrorResponse,
    HealthResponse,
    PipelineStatusResponse,
)

__all__ = [
    "api_router",
    "APIMessage",
    "AnalyzeRequest",
    "AnalyzeSummaryResponse",
    "ArtifactUploadResponse",
    "ErrorResponse",
    "HealthResponse",
    "PipelineStatusResponse",
]