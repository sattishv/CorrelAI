"""
------------------------------------------------------------------------------
CorrelAI

API Router

FastAPI routes for health, artifact upload, and analysis orchestration.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.schemas import (
    APIMessage,
    AnalyzeRequest,
    AnalyzeSummaryResponse,
    ArtifactUploadResponse,
    HealthResponse,
    PipelineStatusResponse,
)
from app.analyzers import (
    CorrelationEngine,
    DependencyGraphBuilder,
    ExtractionPipeline,
    NormalizationPipeline,
    ReplayDiagnosticsEngine,
)
from app.services.artifact_service import ArtifactService

api_router = APIRouter(tags=["CorrelAI"])

_artifact_service = ArtifactService()
_normalization_pipeline = NormalizationPipeline()
_extraction_pipeline = ExtractionPipeline()
_correlation_engine = CorrelationEngine(extraction_pipeline=_extraction_pipeline)
_replay_engine = ReplayDiagnosticsEngine(
    extraction_pipeline=_extraction_pipeline,
    correlation_engine=_correlation_engine,
)
_graph_builder = DependencyGraphBuilder(
    extraction_pipeline=_extraction_pipeline,
    correlation_engine=_correlation_engine,
)


@api_router.get("/", response_model=APIMessage)
def api_root() -> APIMessage:
    """
    Basic API entry point.
    """
    return APIMessage(message="CorrelAI API is running.")


@api_router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Health check endpoint.
    """
    return HealthResponse(status="ok")


@api_router.get("/pipeline/status", response_model=PipelineStatusResponse)
def pipeline_status() -> PipelineStatusResponse:
    """
    Report that the API pipeline components are wired and available.
    """
    return PipelineStatusResponse(
        source="api",
        normalized=True,
        extracted=True,
        correlated=True,
        replay_diagnostics_ready=True,
        dependency_graph_ready=True,
        warnings=[],
    )


@api_router.post("/artifacts/upload", response_model=ArtifactUploadResponse)
async def upload_artifact(file: UploadFile = File(...)) -> ArtifactUploadResponse:
    """
    Accept an uploaded artifact and store it on disk.
    """
    content = await file.read()

    filename = file.filename or "artifact.bin"
    stored_path = _artifact_service.save_bytes(filename=filename, data=content)

    return ArtifactUploadResponse(
        artifact_id=str(uuid4()),
        filename=filename,
        content_type=file.content_type,
        size_bytes=len(content),
        stored_path=str(stored_path),
    )


@api_router.post("/analyze", response_model=AnalyzeSummaryResponse)
def analyze_artifact(request: AnalyzeRequest) -> AnalyzeSummaryResponse:
    """
    Run the analysis pipeline over a stored artifact.
    """
    source_path = _resolve_source_path(request)

    if not source_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {source_path}",
        )

    analyze_anything = (
        request.analyze_normalization
        or request.analyze_extraction
        or request.analyze_correlation
        or request.analyze_replay_diagnostics
        or request.analyze_dependency_graph
    )

    normalization_result = None
    if analyze_anything:
        normalization_result = _normalization_pipeline.normalize(source_path)

    extraction_result = None
    if request.analyze_extraction and normalization_result is not None:
        extraction_result = _extraction_pipeline.extract(normalization_result)

    correlation_result = None
    if request.analyze_correlation and normalization_result is not None:
        correlation_input = extraction_result or normalization_result
        correlation_result = _correlation_engine.correlate(correlation_input)

    replay_result = None
    if request.analyze_replay_diagnostics and normalization_result is not None:
        replay_input = extraction_result or normalization_result
        replay_result = _replay_engine.diagnose(replay_input)

    graph_result = None
    if request.analyze_dependency_graph and normalization_result is not None:
        graph_result = _graph_builder.build(normalization_result)

    warnings: list[str] = []

    if normalization_result is not None and normalization_result.warnings:
        warnings.extend(normalization_result.warnings)

    if extraction_result is not None and extraction_result.warnings:
        warnings.extend(extraction_result.warnings)

    if correlation_result is not None and correlation_result.warnings:
        warnings.extend(correlation_result.warnings)

    if replay_result is not None and replay_result.warnings:
        warnings.extend(replay_result.warnings)

    if graph_result is not None and graph_result.warnings:
        warnings.extend(graph_result.warnings)

    if not analyze_anything:
        warnings.append("No analysis stages were requested.")

    return AnalyzeSummaryResponse(
        source=str(source_path),
        normalization=normalization_result,
        extraction=extraction_result,
        correlation=correlation_result,
        replay_diagnostics=replay_result,
        dependency_graph=graph_result,
        warnings=warnings,
    )


def _resolve_source_path(request: AnalyzeRequest) -> Path:
    """
    Resolve the artifact source path from the API request.

    PR 0013 keeps analysis file-system based. Artifact lookup by ID will come
    later when persistence is introduced.
    """
    if request.stored_path:
        return Path(request.stored_path)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="stored_path is required for analysis in PR 0013.",
    )