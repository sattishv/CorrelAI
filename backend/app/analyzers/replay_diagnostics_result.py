"""
------------------------------------------------------------------------------
CorrelAI

Replay Diagnostics Result

Represents the output of replay diagnostics and failure analysis.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ReplayStatus(str, Enum):
    """
    High-level replay outcome.
    """

    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    UNKNOWN = "unknown"


class ReplayIssueKind(str, Enum):
    """
    Types of replay mismatches or failures.
    """

    MISSING_TOKEN = "missing_token"
    TOKEN_MISMATCH = "token_mismatch"
    HEADER_MISMATCH = "header_mismatch"
    COOKIE_MISMATCH = "cookie_mismatch"
    PARAMETER_MISMATCH = "parameter_mismatch"
    BODY_MISMATCH = "body_mismatch"
    STATUS_MISMATCH = "status_mismatch"
    TIMING_MISMATCH = "timing_mismatch"
    UNKNOWN = "unknown"


class ReplaySeverity(str, Enum):
    """
    Severity of a replay issue.
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReplayIssue(BaseModel):
    """
    Represents a single diagnostic issue discovered during replay analysis.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: ReplayIssueKind = ReplayIssueKind.UNKNOWN
    severity: ReplaySeverity = ReplaySeverity.MEDIUM
    transaction_id: str = Field(..., min_length=1)
    request_name: str = Field(..., min_length=1)
    field_name: str = Field(..., min_length=1)
    expected_value: str = Field(default="", min_length=0)
    observed_value: str = Field(default="", min_length=0)
    message: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplayStepDiagnostics(BaseModel):
    """
    Diagnostics for a single replay step or request.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_id: str = Field(..., min_length=1)
    request_name: str = Field(..., min_length=1)
    status: ReplayStatus = ReplayStatus.UNKNOWN
    issues: list[ReplayIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class ReplayDiagnosticsResult(BaseModel):
    """
    Structured result returned by the replay diagnostics engine.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ReplayStatus = ReplayStatus.UNKNOWN
    step_count: int = Field(default=0, ge=0)
    issue_count: int = Field(default=0, ge=0)
    steps: list[ReplayStepDiagnostics] = Field(default_factory=list)
    issues: list[ReplayIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Keep counts aligned with the diagnostic collections.
        """
        self.step_count = len(self.steps)
        self.issue_count = len(self.issues)