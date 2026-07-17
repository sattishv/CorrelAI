"""
------------------------------------------------------------------------------
CorrelAI

Transaction Domain Model

Represents a complete HTTP transaction containing a request and response.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.request import Request
from app.models.response import Response


class Transaction(BaseModel):
    """Represents a single HTTP transaction."""

    id: str = Field(..., min_length=1)
    request: Request
    response: Response
    name: Optional[str] = None
    source: Optional[str] = None