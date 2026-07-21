"""
------------------------------------------------------------------------------
CorrelAI

Dependency Graph Result

Represents the output of the dependency graph builder.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class GraphNodeKind(str, Enum):
    """
    High-level node types used in the dependency graph.
    """

    TRANSACTION = "transaction"
    VALUE = "value"
    HEADER = "header"
    COOKIE = "cookie"
    PARAMETER = "parameter"
    BODY = "body"
    UNKNOWN = "unknown"


class GraphEdgeKind(str, Enum):
    """
    High-level edge types used in the dependency graph.
    """

    PRODUCES = "produces"
    CONSUMES = "consumes"
    DEPENDS_ON = "depends_on"
    REUSES = "reuses"
    UNKNOWN = "unknown"


class GraphNode(BaseModel):
    """
    Node in the dependency graph.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: GraphNodeKind = GraphNodeKind.UNKNOWN
    label: str = Field(..., min_length=1)
    transaction_id: str | None = None
    value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """
    Directed relationship between graph nodes.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: GraphEdgeKind = GraphEdgeKind.UNKNOWN
    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(default="", min_length=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyGraphResult(BaseModel):
    """
    Structured result returned by the dependency graph builder.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Keep counts aligned with the current graph collections.
        """
        self.node_count = len(self.nodes)
        self.edge_count = len(self.edges)