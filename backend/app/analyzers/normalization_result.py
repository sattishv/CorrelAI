"""
------------------------------------------------------------------------------
CorrelAI

Normalization Result

Represents the output of the normalization pipeline.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.ir.enums import ArtifactType
from app.ir.transaction import Transaction


class NormalizationResult(BaseModel):
    """
    Structured result returned by the normalization pipeline.

    This object is intentionally lightweight and container-friendly. It wraps
    normalized IR transactions together with basic metadata so future analyzers
    can consume a stable contract.
    """

    id: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    artifact_type: ArtifactType
    source: str = Field(..., min_length=1)
    normalized_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_count: int = Field(default=0, ge=0)
    transactions: list[Transaction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Keep the transaction count aligned with the transactions collection.
        """
        self.transaction_count = len(self.transactions)