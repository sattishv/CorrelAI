"""
------------------------------------------------------------------------------
CorrelAI

API Schemas

Request and response models used by the FastAPI layer.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.analyzers import (
    CorrelationResult,
    DependencyGraphResult,
    ExtractionResult,
    NormalizationResult,
    ReplayDiagnosticsResult,
)


class APIMessage(BaseModel):
    """
    Generic API response envelope for simple messages.
    """

    message: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """
    Health check response.
    """

    status: str = Field(default="ok", min_length=1)
    service: str = Field(default="CorrelAI", min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ArtifactUploadResponse(BaseModel):
    """
    Response returned after an artifact has been accepted by the API.
    """

    artifact_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    stored_path: Optional[str] = None
    message: str = Field(default="Artifact uploaded successfully.", min_length=1)


class AnalyzeRequest(BaseModel):
    """
    Request model for analysis endpoints.

    For PR 0013 this is intentionally lightweight. The API will primarily
    reference an uploaded artifact or stored path.
    """

    artifact_id: Optional[str] = None
    stored_path: Optional[str] = None
    filename: Optional[str] = None
    analyze_normalization: bool = True
    analyze_extraction: bool = True
    analyze_correlation: bool = True
    analyze_replay_diagnostics: bool = True
    analyze_dependency_graph: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyzeSummaryResponse(BaseModel):
    """
    Lightweight summary returned by the analysis API.
    """

    source: str
    normalization: Optional[NormalizationResult] = None
    extraction: Optional[ExtractionResult] = None
    correlation: Optional[CorrelationResult] = None
    replay_diagnostics: Optional[ReplayDiagnosticsResult] = None
    dependency_graph: Optional[DependencyGraphResult] = None
    warnings: list[str] = Field(default_factory=list)


class PipelineStatusResponse(BaseModel):
    """
    Response used by pipeline status endpoints.
    """

    artifact_id: Optional[str] = None
    source: Optional[str] = None
    normalized: bool = False
    extracted: bool = False
    correlated: bool = False
    replay_diagnostics_ready: bool = False
    dependency_graph_ready: bool = False
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    error: str = Field(..., min_length=1)
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)