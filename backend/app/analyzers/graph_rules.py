"""
------------------------------------------------------------------------------
CorrelAI

Graph Rules

Defines lightweight rules for filtering and explaining dependency graph items.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.analyzers.dependency_graph_result import (
    GraphEdge,
    GraphEdgeKind,
    GraphNode,
    GraphNodeKind,
)


class GraphMatchMode(str, Enum):
    """
    Strategies used to determine whether a rule applies.
    """

    ANY = "any"
    ALL = "all"


class GraphRule(BaseModel):
    """
    Declarative rule describing a graph filtering or classification pattern.

    The rule system is intentionally lightweight for PR 0011. It is designed to
    keep graph behavior explainable without introducing a complex DSL yet.
    """

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    enabled: bool = True
    node_kinds: list[GraphNodeKind] = Field(default_factory=list)
    edge_kinds: list[GraphEdgeKind] = Field(default_factory=list)
    min_confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    require_transaction_id: bool = False
    require_label_prefix: str | None = None
    match_mode: GraphMatchMode = GraphMatchMode.ANY
    metadata: dict[str, Any] = Field(default_factory=dict)

    def matches_node(self, node: GraphNode) -> bool:
        """
        Check whether this rule applies to a graph node.
        """
        if not self.enabled:
            return False

        checks = [
            not self.node_kinds or node.kind in self.node_kinds,
            not self.require_transaction_id or bool(node.transaction_id),
            not self.require_label_prefix
            or node.label.lower().startswith(self.require_label_prefix.lower()),
        ]

        if self.match_mode == GraphMatchMode.ALL:
            return all(checks)

        return any(checks)

    def matches_edge(self, edge: GraphEdge) -> bool:
        """
        Check whether this rule applies to a graph edge.
        """
        if not self.enabled:
            return False

        checks = [
            not self.edge_kinds or edge.kind in self.edge_kinds,
            edge.confidence >= self.min_confidence,
        ]

        if self.match_mode == GraphMatchMode.ALL:
            return all(checks)

        return any(checks)

    def reason(self) -> str:
        """
        Human-readable explanation for the rule.
        """
        return self.description


class GraphRuleSet(BaseModel):
    """
    Container for graph rules.
    """

    rules: list[GraphRule] = Field(default_factory=list)

    @classmethod
    def default(cls) -> "GraphRuleSet":
        """
        Create a default starter rule set for PR 0011.
        """
        return cls(
            rules=[
                GraphRule(
                    id="rule-transaction-nodes",
                    name="Transaction Nodes",
                    description="Keeps transaction nodes as first-class graph entities.",
                    node_kinds=[GraphNodeKind.TRANSACTION],
                    require_transaction_id=True,
                ),
                GraphRule(
                    id="rule-value-nodes",
                    name="Value Nodes",
                    description="Keeps extracted values visible in the dependency graph.",
                    node_kinds=[
                        GraphNodeKind.VALUE,
                        GraphNodeKind.HEADER,
                        GraphNodeKind.COOKIE,
                        GraphNodeKind.PARAMETER,
                        GraphNodeKind.BODY,
                    ],
                ),
                GraphRule(
                    id="rule-producing-edges",
                    name="Producing Edges",
                    description="Highlights edges where a transaction produces a value.",
                    edge_kinds=[GraphEdgeKind.PRODUCES],
                    min_confidence=0.0,
                ),
                GraphRule(
                    id="rule-consuming-edges",
                    name="Consuming Edges",
                    description="Highlights edges where a transaction consumes a value.",
                    edge_kinds=[GraphEdgeKind.CONSUMES],
                    min_confidence=0.0,
                ),
                GraphRule(
                    id="rule-dependency-edges",
                    name="Dependency Edges",
                    description="Highlights transaction-to-transaction dependency links.",
                    edge_kinds=[
                        GraphEdgeKind.DEPENDS_ON,
                        GraphEdgeKind.REUSES,
                    ],
                    min_confidence=0.60,
                ),
            ]
        )

    def add_rule(self, rule: GraphRule) -> None:
        """
        Add a new rule to the set.
        """
        self.rules.append(rule)

    def enabled_rules(self) -> list[GraphRule]:
        """
        Return only enabled rules.
        """
        return [rule for rule in self.rules if rule.enabled]

    def match_node(self, node: GraphNode) -> list[GraphRule]:
        """
        Return all rules that apply to the given graph node.
        """
        return [rule for rule in self.enabled_rules() if rule.matches_node(node)]

    def match_edge(self, edge: GraphEdge) -> list[GraphRule]:
        """
        Return all rules that apply to the given graph edge.
        """
        return [rule for rule in self.enabled_rules() if rule.matches_edge(edge)]