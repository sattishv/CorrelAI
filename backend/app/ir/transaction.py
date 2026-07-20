"""
------------------------------------------------------------------------------
CorrelAI

IR Transaction

Connects one normalized request and one normalized response.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.ir.entity import Entity
from app.ir.enums import ArtifactType
from app.ir.request import Request
from app.ir.response import Response


class Transaction(Entity):
    artifact_type: ArtifactType = ArtifactType.HAR
    sequence: int = Field(default=0, ge=0)
    request: Request
    response: Response
    name: Optional[str] = None
    page_ref: Optional[str] = None