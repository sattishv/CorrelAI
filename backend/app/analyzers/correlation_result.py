"""
------------------------------------------------------------------------------
CorrelAI

Correlation Result

Represents the output of the correlation engine.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CorrelationKind(str, Enum):
    """
    High-level correlation relationship types.
    """

    TOKEN_REUSE = "token_reuse"
    HEADER_PROPAGATION = "header_propagation"
    COOKIE_PROPAGATION = "cookie_propagation"
    PARAMETER_PROPAGATION = "parameter_propagation"
    BODY_PROPAGATION = "body_propagation"
    UNKNOWN = "unknown"


class CorrelationEvidence(BaseModel):
    """
    Evidence supporting a correlation link.
    """

    extracted_value_id: str = Field(..., min_length=1)
    source_transaction_id: str = Field(..., min_length=1)
    target_transaction_id: str = Field(..., min_length=1)
    source_location: str = Field(..., min_length=1)
    target_location: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    value: str = Field(default="", min_length=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)
    signals: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrelationLink(BaseModel):
    """
    Represents a single candidate correlation between two transactions.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: CorrelationKind = CorrelationKind.UNKNOWN
    source_transaction_id: str = Field(..., min_length=1)
    target_transaction_id: str = Field(..., min_length=1)
    matched_name: str = Field(..., min_length=1)
    matched_value: str = Field(default="", min_length=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[CorrelationEvidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrelationResult(BaseModel):
    """
    Structured result returned by the correlation engine.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_count: int = Field(default=0, ge=0)
    correlation_count: int = Field(default=0, ge=0)
    links: list[CorrelationLink] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Keep the correlation count aligned with the links collection.
        """
        self.correlation_count = len(self.links)