"""
------------------------------------------------------------------------------
CorrelAI

Analyzer Factory

Resolves the appropriate analysis pipeline for a given artifact source.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from app.analyzers.normalization_pipeline import NormalizationPipeline


class AnalyzerFactory:
    """
    Factory for resolving the correct analyzer pipeline for an artifact.

    For PR 0008, all supported artifact types are routed through the
    normalization pipeline. Future versions may dispatch to specialized
    analyzers such as replay analysis, correlation analysis, or diff analysis.
    """

    @staticmethod
    def get_pipeline(source: Union[str, Path]) -> NormalizationPipeline:
        """
        Resolve the analysis pipeline for the given source.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A normalization pipeline instance.
        """
        path = Path(source)
        suffix = path.suffix.lower()

        if suffix in {".har", ".jmx", ".jtl", ".json", ".xml"}:
            return NormalizationPipeline()

        return NormalizationPipeline()