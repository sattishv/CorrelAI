"""
------------------------------------------------------------------------------
CorrelAI

IR Request

Normalized HTTP request representation.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.ir.entity import Entity
from app.models.common import Attachment, Cookie, Header, Parameter


class Request(Entity):
    method: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    http_version: Optional[str] = None
    headers: list[Header] = Field(default_factory=list)
    cookies: list[Cookie] = Field(default_factory=list)
    query_params: list[Parameter] = Field(default_factory=list)
    form_params: list[Parameter] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    body: Optional[str] = None
    content_type: Optional[str] = None
    mime_type: Optional[str] = None
    timestamp: Optional[str] = None
    size_bytes: Optional[int] = None
    is_redirect: bool = False
    redirect_url: Optional[str] = None