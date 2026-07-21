"""
------------------------------------------------------------------------------
CorrelAI

Dependency Graph Builder

Builds a dependency graph from normalized transactions and correlation output.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.analyzers.correlation_engine import CorrelationEngine
from app.analyzers.correlation_result import CorrelationKind
from app.analyzers.dependency_graph_result import (
    DependencyGraphResult,
    GraphEdge,
    GraphEdgeKind,
    GraphNode,
    GraphNodeKind,
)
from app.analyzers.extraction_pipeline import ExtractionPipeline
from app.analyzers.normalization_result import NormalizationResult
from app.analyzers.value_extractor import (
    ExtractedValue,
    ExtractedValueLocation,
    ExtractedValueScope,
)
from app.ir.enums import ArtifactType
from app.ir.transaction import Transaction


class DependencyGraphBuilder:
    """
    Builds a dependency graph from normalized transactions.

    For PR 0011 this builder:
    - accepts normalized IR transactions
    - extracts values
    - correlates values
    - creates graph nodes and edges
    - returns a structured graph result

    The graph is intentionally lightweight and explainable. Later PRs can add
    richer topology, clustering, and visualization-specific metadata.
    """

    def __init__(
        self,
        extraction_pipeline: ExtractionPipeline | None = None,
        correlation_engine: CorrelationEngine | None = None,
    ) -> None:
        self._extraction_pipeline = extraction_pipeline or ExtractionPipeline()
        self._correlation_engine = correlation_engine or CorrelationEngine(
            extraction_pipeline=self._extraction_pipeline
        )

    def build(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> DependencyGraphResult:
        """
        Build a dependency graph from a normalized source.
        """
        normalization_result = self._resolve_source(source)

        extraction_result = self._extraction_pipeline.extract(normalization_result)
        correlation_result = self._correlation_engine.correlate(normalization_result)

        transaction_nodes = self._build_transaction_nodes(normalization_result.transactions)
        value_nodes = self._build_value_nodes(extraction_result.values)
        edges = self._build_edges(
            transactions=normalization_result.transactions,
            values=extraction_result.values,
            correlation_links=correlation_result.links,
        )

        nodes = transaction_nodes + value_nodes
        warnings: list[str] = []

        if not normalization_result.transactions:
            warnings.append("No transactions were available for graph construction.")
        if not value_nodes:
            warnings.append("No extracted values were available for graph construction.")
        if not edges:
            warnings.append("No dependency relationships were discovered.")

        return DependencyGraphResult(
            source=normalization_result.source,
            nodes=nodes,
            edges=edges,
            warnings=warnings,
            metadata={
                "artifact_type": normalization_result.artifact_type.value,
                "transaction_count": len(normalization_result.transactions),
                "value_count": extraction_result.value_count,
                "correlation_count": correlation_result.correlation_count,
            },
        )

    def summarize(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> dict[str, Any]:
        """
        Return a lightweight summary suitable for APIs or previews.
        """
        result = self.build(source)

        return {
            "id": result.id,
            "source": result.source,
            "generated_at": result.generated_at.isoformat(),
            "node_count": result.node_count,
            "edge_count": result.edge_count,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }

    def _resolve_source(
        self,
        source: NormalizationResult | Iterable[Transaction],
    ) -> NormalizationResult:
        """
        Resolve any supported source into a NormalizationResult.
        """
        if isinstance(source, NormalizationResult):
            return source

        transactions = list(source)
        return NormalizationResult(
            artifact_type=ArtifactType.TRACE,
            source="memory",
            transactions=transactions,
        )

    def _build_transaction_nodes(
        self,
        transactions: list[Transaction],
    ) -> list[GraphNode]:
        """
        Build graph nodes for transactions.
        """
        nodes: list[GraphNode] = []

        for transaction in transactions:
            label = transaction.name or f"{transaction.request.method} {transaction.request.url}".strip()
            if not label:
                label = f"Transaction {transaction.sequence}"

            nodes.append(
                GraphNode(
                    id=transaction.id,
                    kind=GraphNodeKind.TRANSACTION,
                    label=label,
                    transaction_id=transaction.id,
                    metadata={
                        "artifact_type": transaction.artifact_type.value,
                        "sequence": transaction.sequence,
                    },
                )
            )

        return nodes

    def _build_value_nodes(
        self,
        values: list[ExtractedValue],
    ) -> list[GraphNode]:
        """
        Build graph nodes for extracted values.
        """
        nodes: list[GraphNode] = []

        for value in values:
            nodes.append(
                GraphNode(
                    id=value.id,
                    kind=self._map_value_location_to_node_kind(value.location),
                    label=self._build_value_label(value),
                    transaction_id=value.transaction_id,
                    value=value.value,
                    metadata={
                        "location": value.location.value,
                        "scope": value.scope.value,
                        "name": value.name,
                        "classification": value.metadata.get("classification", {}),
                    },
                )
            )

        return nodes

    def _build_edges(
        self,
        transactions: list[Transaction],
        values: list[ExtractedValue],
        correlation_links: list[Any],
    ) -> list[GraphEdge]:
        """
        Build graph edges from extracted values and correlation links.
        """
        edges: list[GraphEdge] = []

        # Transaction -> Value edges
        for value in values:
            edge_kind = (
                GraphEdgeKind.PRODUCES
                if value.scope == ExtractedValueScope.RESPONSE
                else GraphEdgeKind.CONSUMES
            )

            edges.append(
                GraphEdge(
                    kind=edge_kind,
                    source_node_id=value.transaction_id,
                    target_node_id=value.id,
                    confidence=1.0,
                    reason=f"Value extracted from {value.scope.value}:{value.location.value}.",
                    metadata={
                        "location": value.location.value,
                        "scope": value.scope.value,
                        "name": value.name,
                    },
                )
            )

        # Transaction -> Transaction edges from correlation links
        for link in correlation_links:
            edge_kind = self._map_correlation_kind_to_edge_kind(link.kind)

            reason = "Correlation discovered between producer and consumer transactions."
            if link.evidence:
                reason = link.evidence[0].reason

            edges.append(
                GraphEdge(
                    kind=edge_kind,
                    source_node_id=link.source_transaction_id,
                    target_node_id=link.target_transaction_id,
                    confidence=link.confidence,
                    reason=reason,
                    metadata={
                        "correlation_kind": link.kind.value,
                        "matched_name": link.matched_name,
                        "matched_value": link.matched_value,
                        "evidence_count": len(link.evidence),
                    },
                )
            )

        return edges

    def _map_value_location_to_node_kind(
        self,
        location: ExtractedValueLocation,
    ) -> GraphNodeKind:
        """
        Map extracted value location to graph node kind.
        """
        if location == ExtractedValueLocation.HEADER:
            return GraphNodeKind.HEADER
        if location == ExtractedValueLocation.COOKIE:
            return GraphNodeKind.COOKIE
        if location in {
            ExtractedValueLocation.QUERY_PARAM,
            ExtractedValueLocation.FORM_PARAM,
        }:
            return GraphNodeKind.PARAMETER
        if location in {
            ExtractedValueLocation.BODY,
            ExtractedValueLocation.BODY_JSON,
        }:
            return GraphNodeKind.BODY

        return GraphNodeKind.VALUE

    def _map_correlation_kind_to_edge_kind(
        self,
        kind: CorrelationKind,
    ) -> GraphEdgeKind:
        """
        Map correlation kind to graph edge kind.
        """
        if kind == CorrelationKind.TOKEN_REUSE:
            return GraphEdgeKind.REUSES
        if kind == CorrelationKind.HEADER_PROPAGATION:
            return GraphEdgeKind.DEPENDS_ON
        if kind == CorrelationKind.COOKIE_PROPAGATION:
            return GraphEdgeKind.DEPENDS_ON
        if kind == CorrelationKind.PARAMETER_PROPAGATION:
            return GraphEdgeKind.DEPENDS_ON
        if kind == CorrelationKind.BODY_PROPAGATION:
            return GraphEdgeKind.DEPENDS_ON

        return GraphEdgeKind.UNKNOWN

    def _build_value_label(self, value: ExtractedValue) -> str:
        """
        Build a readable label for a value node.
        """
        name = value.name.strip() or "value"
        preview = value.value.strip()

        if len(preview) > 60:
            preview = f"{preview[:57]}..."

        if preview:
            return f"{name} = {preview}"

        return name