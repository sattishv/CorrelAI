"""
------------------------------------------------------------------------------
CorrelAI

Extraction Result

Represents the output of the value extraction engine.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.analyzers.value_extractor import ExtractedValue


class ExtractionResult(BaseModel):
    """
    Structured result returned by the value extraction engine.

    This object wraps extracted values together with lightweight metadata so
    downstream analyzers can work with a stable contract.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(..., min_length=1)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    value_count: int = Field(default=0, ge=0)
    values: list[ExtractedValue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Keep the value count aligned with the extracted values collection.
        """
        self.value_count = len(self.values)