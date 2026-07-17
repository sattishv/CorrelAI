"""
------------------------------------------------------------------------------
CorrelAI

HAR File Domain Model

Represents a complete HAR capture containing multiple HTTP transactions.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.transaction import Transaction


class HarFile(BaseModel):
    """Represents a HAR file and its parsed transactions."""

    filename: str = Field(..., min_length=1)
    version: Optional[str] = None
    creator_name: Optional[str] = None
    creator_version: Optional[str] = None
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None
    page_count: int = 0
    transaction_count: int = 0
    transactions: list[Transaction] = Field(default_factory=list)