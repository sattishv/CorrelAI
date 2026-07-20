"""
------------------------------------------------------------------------------
CorrelAI

IR Response

Normalized HTTP response representation.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.ir.entity import Entity
from app.models.common import Cookie, Header


class Response(Entity):
    status_code: int = Field(..., ge=100, le=599)
    status_text: Optional[str] = None
    http_version: Optional[str] = None
    headers: list[Header] = Field(default_factory=list)
    cookies: list[Cookie] = Field(default_factory=list)
    body: Optional[str] = None
    content_type: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    redirect_url: Optional[str] = None
    is_redirect: bool = False
    timestamp: Optional[str] = None