"""
------------------------------------------------------------------------------
CorrelAI

Normalization Pipeline

Converts parsed artifacts into a normalized IR-backed result.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.analyzers.normalization_result import NormalizationResult
from app.ir.enums import ArtifactType
from app.ir.transaction import Transaction
from app.services.parser_service import ParserService


class NormalizationPipeline:
    """
    Normalizes source artifacts into a consistent IR-based result.

    For PR 0008, this pipeline is intentionally thin:
    - parse the artifact
    - wrap the IR transactions in a structured result
    - collect lightweight metadata and warnings

    Later versions will enrich this pipeline with:
    - field normalization
    - content extraction
    - dynamic value detection hooks
    - dependency enrichment
    """

    def __init__(self, parser_service: ParserService | None = None) -> None:
        self._parser_service = parser_service or ParserService()

    def normalize(self, source: str | Path) -> NormalizationResult:
        """
        Normalize the given artifact source.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A NormalizationResult containing normalized IR transactions.
        """
        path = Path(source)
        transactions: list[Transaction] = self._parser_service.parse(path)

        artifact_type = self._detect_artifact_type(path)

        warnings: list[str] = []
        if not transactions:
            warnings.append("No transactions were discovered in the artifact.")

        return NormalizationResult(
            artifact_type=artifact_type,
            source=str(path),
            transactions=transactions,
            warnings=warnings,
            metadata={
                "file_name": path.name,
                "file_suffix": path.suffix.lower(),
            },
        )

    def summarize(self, source: str | Path) -> dict[str, Any]:
        """
        Return a lightweight summary for the normalized artifact.

        This is useful for API responses and early-stage UI previews.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A dictionary summary of the normalized artifact.
        """
        result = self.normalize(source)

        return {
            "id": result.id,
            "artifact_type": result.artifact_type.value,
            "source": result.source,
            "normalized_at": result.normalized_at.isoformat(),
            "transaction_count": result.transaction_count,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }

    def _detect_artifact_type(self, path: Path) -> ArtifactType:
        """
        Detect the artifact type from the file extension.

        Args:
            path: Artifact path.

        Returns:
            The matching ArtifactType.
        """
        suffix = path.suffix.lower()

        if suffix == ".har":
            return ArtifactType.HAR

        if suffix == ".jmx":
            return ArtifactType.JMX

        if suffix == ".jtl":
            return ArtifactType.JTL

        return ArtifactType.TRACE