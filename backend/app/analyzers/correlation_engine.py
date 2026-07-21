"""
------------------------------------------------------------------------------
CorrelAI

Correlation Engine

Discovers candidate relationships between extracted values and transactions.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from app.analyzers.correlation_result import (
    CorrelationEvidence,
    CorrelationKind,
    CorrelationLink,
    CorrelationResult,
)
from app.analyzers.extraction_result import ExtractionResult
from app.analyzers.value_classifier import ValueCategory, ValueClassification
from app.analyzers.value_extractor import ExtractedValue, ExtractedValueLocation, ExtractedValueScope
from app.analyzers.extraction_pipeline import ExtractionPipeline
from app.analyzers.normalization_result import NormalizationResult
from app.ir.transaction import Transaction


class CorrelationEngine:
    """
    Heuristic correlation engine.

    The engine looks for likely producer/consumer relationships across
    transactions using extracted values and lightweight classifications.

    For PR 0010, the goal is not perfect correlation. The goal is to create
    a stable, explainable foundation that can later grow into a richer engine.
    """

    def __init__(self, extraction_pipeline: ExtractionPipeline | None = None) -> None:
        self._extraction_pipeline = extraction_pipeline or ExtractionPipeline()

    def correlate(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> CorrelationResult:
        """
        Correlate extracted values across transactions.

        Args:
            source: Normalized result, extraction result, or transaction iterable.

        Returns:
            CorrelationResult containing candidate correlation links.
        """
        source_name, extraction_result = self._resolve_source(source)

        values = extraction_result.values
        links: list[CorrelationLink] = []

        # Group candidate values by normalized signal to compare cross-transaction reuse.
        grouped = self._group_values(values)

        for key, group in grouped.items():
            if len(group) < 2:
                continue

            links.extend(self._build_links_for_group(key, group))

        warnings: list[str] = []
        if not values:
            warnings.append("No extracted values were available for correlation.")
        if not links:
            warnings.append("No candidate correlations were discovered.")

        return CorrelationResult(
            source=source_name,
            links=links,
            warnings=warnings,
            metadata={
                "transaction_count": extraction_result.metadata.get("transaction_count", 0),
                "value_count": extraction_result.value_count,
                "classification_summary": extraction_result.metadata.get("classification_summary", {}),
            },
        )

    def summarize(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> dict[str, Any]:
        """
        Return a lightweight summary suitable for API responses or previews.
        """
        result = self.correlate(source)

        return {
            "id": result.id,
            "source": result.source,
            "generated_at": result.generated_at.isoformat(),
            "correlation_count": result.correlation_count,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }

    def _resolve_source(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> tuple[str, ExtractionResult]:
        """
        Resolve input into a source name and an extraction result.
        """
        if isinstance(source, ExtractionResult):
            return source.source, source

        if isinstance(source, NormalizationResult):
            extraction_result = self._extraction_pipeline.extract(source)
            return source.source, extraction_result

        transactions = list(source)
        normalization_result = NormalizationResult(
            artifact_type=self._detect_artifact_type(),
            source="memory",
            transactions=transactions,
        )
        extraction_result = self._extraction_pipeline.extract(normalization_result)
        return "memory", extraction_result

    def _detect_artifact_type(self):
        """
        Placeholder artifact type for in-memory transaction sources.
        """
        from app.ir.enums import ArtifactType

        return ArtifactType.TRACE

    def _group_values(self, values: list[ExtractedValue]) -> dict[str, list[ExtractedValue]]:
        """
        Group values by normalized correlation key.
        """
        grouped: dict[str, list[ExtractedValue]] = defaultdict(list)

        for value in values:
            key = self._build_group_key(value)
            grouped[key].append(value)

        return grouped

    def _build_group_key(self, value: ExtractedValue) -> str:
        """
        Build a stable grouping key for a value.
        """
        name = value.name.strip().lower()
        raw = value.value.strip()

        classification = value.metadata.get("classification", {})
        category = classification.get("category", ValueCategory.OTHER.value)

        location = value.location.value
        scope = value.scope.value

        # Keep the key simple and explainable for now.
        return f"{category}|{name}|{raw}|{location}|{scope}"

    def _build_links_for_group(
        self,
        group_key: str,
        group: list[ExtractedValue],
    ) -> list[CorrelationLink]:
        """
        Build correlation links from a group of related extracted values.
        """
        links: list[CorrelationLink] = []

        sorted_group = sorted(
            group,
            key=lambda item: (
                item.transaction_id,
                item.location.value,
                item.scope.value,
                item.name.lower(),
            ),
        )

        producer_candidates = [
            item
            for item in sorted_group
            if item.scope == ExtractedValueScope.RESPONSE
        ]
        consumer_candidates = [
            item
            for item in sorted_group
            if item.scope == ExtractedValueScope.REQUEST
        ]

        if not producer_candidates or not consumer_candidates:
            return links

        for producer in producer_candidates:
            for consumer in consumer_candidates:
                if producer.transaction_id == consumer.transaction_id:
                    continue

                kind = self._infer_kind(producer, consumer)
                confidence = self._score_pair(producer, consumer, kind)

                if confidence < 0.60:
                    continue

                links.append(
                    CorrelationLink(
                        kind=kind,
                        source_transaction_id=producer.transaction_id,
                        target_transaction_id=consumer.transaction_id,
                        matched_name=consumer.name,
                        matched_value=consumer.value,
                        confidence=confidence,
                        evidence=[
                            CorrelationEvidence(
                                extracted_value_id=producer.id,
                                source_transaction_id=producer.transaction_id,
                                target_transaction_id=consumer.transaction_id,
                                source_location=producer.location.value,
                                target_location=consumer.location.value,
                                name=consumer.name,
                                value=consumer.value,
                                confidence=confidence,
                                reason="Value appears in a response and is later reused in a request.",
                                signals=self._collect_signals(producer, consumer, group_key),
                                metadata={
                                    "group_key": group_key,
                                },
                            )
                        ],
                        metadata={
                            "producer_scope": producer.scope.value,
                            "consumer_scope": consumer.scope.value,
                            "producer_category": self._get_category(producer),
                            "consumer_category": self._get_category(consumer),
                        },
                    )
                )

        return links

    def _infer_kind(
        self,
        producer: ExtractedValue,
        consumer: ExtractedValue,
    ) -> CorrelationKind:
        """
        Infer a coarse correlation type from the value locations and categories.
        """
        producer_category = self._get_category(producer)
        consumer_category = self._get_category(consumer)

        if producer_category in {ValueCategory.AUTH_TOKEN.value, ValueCategory.SESSION_ID.value}:
            return CorrelationKind.TOKEN_REUSE

        if consumer.location == ExtractedValueLocation.HEADER:
            return CorrelationKind.HEADER_PROPAGATION

        if consumer.location == ExtractedValueLocation.COOKIE:
            return CorrelationKind.COOKIE_PROPAGATION

        if consumer.location in {
            ExtractedValueLocation.QUERY_PARAM,
            ExtractedValueLocation.FORM_PARAM,
        }:
            return CorrelationKind.PARAMETER_PROPAGATION

        if consumer.location in {ExtractedValueLocation.BODY, ExtractedValueLocation.BODY_JSON}:
            return CorrelationKind.BODY_PROPAGATION

        # Default based on value category.
        if producer_category == ValueCategory.CSRF_TOKEN.value or consumer_category == ValueCategory.CSRF_TOKEN.value:
            return CorrelationKind.TOKEN_REUSE

        return CorrelationKind.UNKNOWN

    def _score_pair(
        self,
        producer: ExtractedValue,
        consumer: ExtractedValue,
        kind: CorrelationKind,
    ) -> float:
        """
        Score the strength of a candidate correlation.
        """
        score = 0.60

        if producer.name.strip().lower() == consumer.name.strip().lower():
            score += 0.15

        if producer.value.strip() == consumer.value.strip():
            score += 0.10

        if producer.location != consumer.location:
            score += 0.05

        if kind != CorrelationKind.UNKNOWN:
            score += 0.05

        if self._get_category(producer) == self._get_category(consumer):
            score += 0.05

        return min(score, 0.99)

    def _collect_signals(
        self,
        producer: ExtractedValue,
        consumer: ExtractedValue,
        group_key: str,
    ) -> list[str]:
        """
        Collect explainability signals for a candidate correlation.
        """
        signals: list[str] = []

        producer_category = self._get_category(producer)
        consumer_category = self._get_category(consumer)

        signals.append(f"producer:{producer.scope.value}:{producer.location.value}")
        signals.append(f"consumer:{consumer.scope.value}:{consumer.location.value}")
        signals.append(f"category:{producer_category}")
        signals.append(f"group_key:{group_key}")

        if producer.name.strip().lower() == consumer.name.strip().lower():
            signals.append("matching-name")

        if producer.value.strip() == consumer.value.strip():
            signals.append("matching-value")

        if producer_category == consumer_category:
            signals.append("matching-category")

        return signals

    def _get_category(self, value: ExtractedValue) -> str:
        """
        Read the classification category attached to an extracted value.
        """
        classification = value.metadata.get("classification", {})
        return str(classification.get("category", ValueCategory.OTHER.value)).lower()