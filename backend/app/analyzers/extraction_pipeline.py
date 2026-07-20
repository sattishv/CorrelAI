"""
------------------------------------------------------------------------------
CorrelAI

Extraction Pipeline

Coordinates value extraction and lightweight classification.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from app.analyzers.extraction_result import ExtractionResult
from app.analyzers.normalization_result import NormalizationResult
from app.analyzers.value_classifier import ValueClassifier, ValueClassification
from app.analyzers.value_extractor import ExtractedValue, ValueExtractor
from app.ir.enums import ArtifactType
from app.ir.transaction import Transaction


class ExtractionPipeline:
    """
    Orchestrates extraction and classification of candidate values.

    For PR 0009 this pipeline:
    - accepts normalized IR transactions
    - extracts candidate values
    - classifies them using lightweight heuristics
    - wraps the result in a stable ExtractionResult
    """

    def __init__(
        self,
        extractor: ValueExtractor | None = None,
        classifier: ValueClassifier | None = None,
    ) -> None:
        self._extractor = extractor or ValueExtractor()
        self._classifier = classifier or ValueClassifier()

    def extract(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> ExtractionResult:
        """
        Extract and classify values from a normalized source.
        """
        source_name, artifact_type, transactions = self._resolve_source(source)

        values = self._extractor.extract_many(transactions)
        classifications = self._classifier.classify_many(values)

        self._annotate_values(values, classifications)

        summary = Counter(item.category.value for item in classifications)
        warnings: list[str] = []

        if not transactions:
            warnings.append("No transactions were provided to the extraction pipeline.")

        if not values:
            warnings.append("No candidate values were extracted from the transactions.")

        return ExtractionResult(
            source=source_name,
            values=values,
            warnings=warnings,
            metadata={
                "artifact_type": artifact_type.value,
                "transaction_count": len(transactions),
                "value_count": len(values),
                "classification_summary": dict(summary),
                "classification_count": len(classifications),
            },
        )

    def summarize(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> dict[str, Any]:
        """
        Return a lightweight summary suitable for API responses or previews.
        """
        result = self.extract(source)

        return {
            "id": result.id,
            "source": result.source,
            "extracted_at": result.extracted_at.isoformat(),
            "value_count": result.value_count,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }

    def _resolve_source(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> tuple[str, ArtifactType, list[Transaction]]:
        """
        Resolve input into a source name, artifact type, and list of transactions.
        """
        if isinstance(source, NormalizationResult):
            return source.source, source.artifact_type, list(source.transactions)

        transactions = list(source)
        return "memory", ArtifactType.TRACE, transactions

    def _annotate_values(
        self,
        values: list[ExtractedValue],
        classifications: list[ValueClassification],
    ) -> None:
        """
        Attach classification metadata to each extracted value.
        """
        classification_map = {
            classification.extracted_value_id: classification
            for classification in classifications
        }

        for value in values:
            classification = classification_map.get(value.id)
            if classification is None:
                continue

            value.metadata["classification"] = {
                "category": classification.category.value,
                "confidence": classification.confidence,
                "reason": classification.reason,
                "signals": classification.signals,
            }