"""
------------------------------------------------------------------------------
CorrelAI

IR Entity Base

Base class for all Intermediate Representation entities.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None