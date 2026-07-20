"""
------------------------------------------------------------------------------
CorrelAI

IR Graph

Graph primitives for dependency and correlation analysis.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.ir.entity import Entity


class GraphNode(Entity):
    label: str = Field(..., min_length=1)
    node_type: str = Field(..., min_length=1)
    ref_id: Optional[str] = None


class GraphEdge(Entity):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    edge_type: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)