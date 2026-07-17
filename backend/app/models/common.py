"""
------------------------------------------------------------------------------
CorrelAI

Common Domain Models

Reusable foundational models used across request/response parsing and analysis.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Header(BaseModel):
    """Represents a single HTTP header."""

    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=0)


class Cookie(BaseModel):
    """Represents a single HTTP cookie."""

    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=0)
    domain: Optional[str] = None
    path: Optional[str] = None
    expires: Optional[datetime] = None
    http_only: bool = False
    secure: bool = False


class Parameter(BaseModel):
    """Represents a request parameter (query/form/path)."""

    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=0)


class Attachment(BaseModel):
    """Represents a file attachment or uploaded multipart part."""

    filename: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None