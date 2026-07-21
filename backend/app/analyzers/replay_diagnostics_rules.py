"""
------------------------------------------------------------------------------
CorrelAI

Replay Diagnostics Rules

Defines lightweight rules used to interpret replay issues and step health.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.analyzers.replay_diagnostics_result import (
    ReplayIssue,
    ReplayIssueKind,
    ReplaySeverity,
    ReplayStatus,
    ReplayStepDiagnostics,
)


class ReplayMatchMode(str, Enum):
    """
    Strategies used to determine whether a rule applies.
    """

    ANY = "any"
    ALL = "all"


class ReplayRule(BaseModel):
    """
    Declarative rule describing a replay diagnostic pattern.

    The rule system is intentionally lightweight for PR 0012. It is designed to
    keep replay behavior explainable without introducing a heavy rule DSL yet.
    """

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    enabled: bool = True
    issue_kinds: list[ReplayIssueKind] = Field(default_factory=list)
    severities: list[ReplaySeverity] = Field(default_factory=list)
    statuses: list[ReplayStatus] = Field(default_factory=list)
    min_confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    require_transaction_id: bool = False
    require_field_name_prefix: str | None = None
    require_message_prefix: str | None = None
    match_mode: ReplayMatchMode = ReplayMatchMode.ANY
    metadata: dict[str, Any] = Field(default_factory=dict)

    def matches_issue(self, issue: ReplayIssue) -> bool:
        """
        Check whether this rule applies to a replay issue.
        """
        if not self.enabled:
            return False

        checks = [
            not self.issue_kinds or issue.kind in self.issue_kinds,
            not self.severities or issue.severity in self.severities,
            issue.confidence >= self.min_confidence,
            not self.require_transaction_id or bool(issue.transaction_id),
            not self.require_field_name_prefix
            or issue.field_name.lower().startswith(self.require_field_name_prefix.lower()),
            not self.require_message_prefix
            or issue.message.lower().startswith(self.require_message_prefix.lower()),
        ]

        if self.match_mode == ReplayMatchMode.ALL:
            return all(checks)

        return any(checks)

    def matches_step(self, step: ReplayStepDiagnostics) -> bool:
        """
        Check whether this rule applies to a replay step.
        """
        if not self.enabled:
            return False

        checks = [
            not self.statuses or step.status in self.statuses,
            not self.require_transaction_id or bool(step.transaction_id),
        ]

        if self.match_mode == ReplayMatchMode.ALL:
            return all(checks)

        return any(checks)

    def reason(self) -> str:
        """
        Human-readable explanation for the rule.
        """
        return self.description


class ReplayRuleSet(BaseModel):
    """
    Container for replay diagnostic rules.
    """

    rules: list[ReplayRule] = Field(default_factory=list)

    @classmethod
    def default(cls) -> "ReplayRuleSet":
        """
        Create a default starter rule set for PR 0012.
        """
        return cls(
            rules=[
                ReplayRule(
                    id="rule-missing-token",
                    name="Missing Token",
                    description="Highlights replay issues caused by missing sensitive tokens.",
                    issue_kinds=[
                        ReplayIssueKind.MISSING_TOKEN,
                        ReplayIssueKind.TOKEN_MISMATCH,
                    ],
                    severities=[
                        ReplaySeverity.HIGH,
                        ReplaySeverity.CRITICAL,
                    ],
                ),
                ReplayRule(
                    id="rule-header-mismatch",
                    name="Header Mismatch",
                    description="Highlights request header mismatches during replay.",
                    issue_kinds=[ReplayIssueKind.HEADER_MISMATCH],
                    severities=[
                        ReplaySeverity.MEDIUM,
                        ReplaySeverity.HIGH,
                        ReplaySeverity.CRITICAL,
                    ],
                ),
                ReplayRule(
                    id="rule-cookie-mismatch",
                    name="Cookie Mismatch",
                    description="Highlights cookie drift during replay.",
                    issue_kinds=[ReplayIssueKind.COOKIE_MISMATCH],
                    severities=[
                        ReplaySeverity.MEDIUM,
                        ReplaySeverity.HIGH,
                        ReplaySeverity.CRITICAL,
                    ],
                ),
                ReplayRule(
                    id="rule-parameter-mismatch",
                    name="Parameter Mismatch",
                    description="Highlights query and form parameter mismatches.",
                    issue_kinds=[ReplayIssueKind.PARAMETER_MISMATCH],
                    severities=[
                        ReplaySeverity.MEDIUM,
                        ReplaySeverity.HIGH,
                    ],
                ),
                ReplayRule(
                    id="rule-body-mismatch",
                    name="Body Mismatch",
                    description="Highlights request body mismatches.",
                    issue_kinds=[ReplayIssueKind.BODY_MISMATCH],
                    severities=[
                        ReplaySeverity.MEDIUM,
                        ReplaySeverity.HIGH,
                        ReplaySeverity.CRITICAL,
                    ],
                ),
                ReplayRule(
                    id="rule-status-mismatch",
                    name="Status Mismatch",
                    description="Highlights HTTP status code mismatches.",
                    issue_kinds=[ReplayIssueKind.STATUS_MISMATCH],
                    severities=[
                        ReplaySeverity.MEDIUM,
                        ReplaySeverity.HIGH,
                    ],
                ),
                ReplayRule(
                    id="rule-pass-steps",
                    name="Healthy Replay Step",
                    description="Highlights steps that passed replay diagnostics.",
                    statuses=[ReplayStatus.PASS],
                    min_confidence=0.0,
                ),
            ]
        )

    def add_rule(self, rule: ReplayRule) -> None:
        """
        Add a new rule to the set.
        """
        self.rules.append(rule)

    def enabled_rules(self) -> list[ReplayRule]:
        """
        Return only enabled rules.
        """
        return [rule for rule in self.rules if rule.enabled]

    def match_issue(self, issue: ReplayIssue) -> list[ReplayRule]:
        """
        Return all rules that apply to the given replay issue.
        """
        return [rule for rule in self.enabled_rules() if rule.matches_issue(issue)]

    def match_step(self, step: ReplayStepDiagnostics) -> list[ReplayRule]:
        """
        Return all rules that apply to the given replay step.
        """
        return [rule for rule in self.enabled_rules() if rule.matches_step(step)]