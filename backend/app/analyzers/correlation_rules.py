"""
------------------------------------------------------------------------------
CorrelAI

Correlation Rules

Defines lightweight rules used by the correlation engine to explain and
classify candidate relationships.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.analyzers.correlation_result import CorrelationKind
from app.analyzers.value_classifier import ValueCategory
from app.analyzers.value_extractor import ExtractedValue


class CorrelationMatchMode(str, Enum):
    """
    Strategies used to determine whether a rule applies.
    """

    ANY = "any"
    ALL = "all"


class CorrelationRule(BaseModel):
    """
    Declarative rule describing a candidate correlation pattern.

    The rule is intentionally lightweight for PR 0010. It is designed to help
    the engine explain why two values may be related, without introducing a
    heavy rule DSL yet.
    """

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    enabled: bool = True
    kind: CorrelationKind = CorrelationKind.UNKNOWN
    min_confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    producer_categories: list[ValueCategory] = Field(default_factory=list)
    consumer_categories: list[ValueCategory] = Field(default_factory=list)
    producer_locations: list[str] = Field(default_factory=list)
    consumer_locations: list[str] = Field(default_factory=list)
    require_matching_name: bool = False
    require_matching_value: bool = False
    match_mode: CorrelationMatchMode = CorrelationMatchMode.ANY
    metadata: dict[str, Any] = Field(default_factory=dict)

    def matches(
        self,
        producer: ExtractedValue,
        consumer: ExtractedValue,
        kind: CorrelationKind,
        confidence: float,
    ) -> bool:
        """
        Check whether this rule applies to a candidate correlation.
        """
        if not self.enabled:
            return False

        if self.kind != CorrelationKind.UNKNOWN and self.kind != kind:
            return False

        if confidence < self.min_confidence:
            return False

        producer_category = self._get_category(producer)
        consumer_category = self._get_category(consumer)

        checks = [
            not self.producer_categories or producer_category in self.producer_categories,
            not self.consumer_categories or consumer_category in self.consumer_categories,
            not self.producer_locations
            or producer.location.value in self.producer_locations,
            not self.consumer_locations
            or consumer.location.value in self.consumer_locations,
            not self.require_matching_name
            or producer.name.strip().lower() == consumer.name.strip().lower(),
            not self.require_matching_value
            or producer.value.strip() == consumer.value.strip(),
        ]

        if self.match_mode == CorrelationMatchMode.ALL:
            return all(checks)

        return any(checks)

    def reason(self) -> str:
        """
        Human-readable explanation for the rule.
        """
        return self.description

    def _get_category(self, value: ExtractedValue) -> ValueCategory:
        """
        Read the classification category from an extracted value.
        """
        classification = value.metadata.get("classification", {})
        raw_category = str(classification.get("category", ValueCategory.OTHER.value)).lower()

        for category in ValueCategory:
            if category.value == raw_category:
                return category

        return ValueCategory.OTHER


class CorrelationRuleSet(BaseModel):
    """
    Container for correlation rules.
    """

    rules: list[CorrelationRule] = Field(default_factory=list)

    @classmethod
    def default(cls) -> "CorrelationRuleSet":
        """
        Create a default starter rule set for PR 0010.
        """
        return cls(
            rules=[
                CorrelationRule(
                    id="rule-token-reuse",
                    name="Token Reuse",
                    description=(
                        "Detects values that look like auth, session, or CSRF tokens "
                        "being produced by a response and reused later in a request."
                    ),
                    kind=CorrelationKind.TOKEN_REUSE,
                    min_confidence=0.60,
                    producer_categories=[
                        ValueCategory.AUTH_TOKEN,
                        ValueCategory.SESSION_ID,
                        ValueCategory.CSRF_TOKEN,
                    ],
                    consumer_categories=[
                        ValueCategory.AUTH_TOKEN,
                        ValueCategory.SESSION_ID,
                        ValueCategory.CSRF_TOKEN,
                    ],
                ),
                CorrelationRule(
                    id="rule-header-propagation",
                    name="Header Propagation",
                    description=(
                        "Detects values reused in HTTP headers across transactions."
                    ),
                    kind=CorrelationKind.HEADER_PROPAGATION,
                    min_confidence=0.60,
                    producer_locations=["header", "cookie", "body_json"],
                    consumer_locations=["header"],
                ),
                CorrelationRule(
                    id="rule-cookie-propagation",
                    name="Cookie Propagation",
                    description=(
                        "Detects values reused in cookie containers across transactions."
                    ),
                    kind=CorrelationKind.COOKIE_PROPAGATION,
                    min_confidence=0.60,
                    producer_locations=["cookie", "body_json"],
                    consumer_locations=["cookie"],
                ),
                CorrelationRule(
                    id="rule-parameter-propagation",
                    name="Parameter Propagation",
                    description=(
                        "Detects values reused in query or form parameters."
                    ),
                    kind=CorrelationKind.PARAMETER_PROPAGATION,
                    min_confidence=0.60,
                    producer_locations=["header", "cookie", "body_json"],
                    consumer_locations=["query_param", "form_param"],
                ),
                CorrelationRule(
                    id="rule-body-propagation",
                    name="Body Propagation",
                    description=(
                        "Detects values copied into request bodies or JSON payloads."
                    ),
                    kind=CorrelationKind.BODY_PROPAGATION,
                    min_confidence=0.60,
                    producer_locations=["header", "cookie", "query_param", "form_param", "body_json"],
                    consumer_locations=["body", "body_json"],
                ),
            ]
        )

    def add_rule(self, rule: CorrelationRule) -> None:
        """
        Add a new rule to the set.
        """
        self.rules.append(rule)

    def enabled_rules(self) -> list[CorrelationRule]:
        """
        Return only enabled rules.
        """
        return [rule for rule in self.rules if rule.enabled]

    def match(
        self,
        producer: ExtractedValue,
        consumer: ExtractedValue,
        kind: CorrelationKind,
        confidence: float,
    ) -> list[CorrelationRule]:
        """
        Return all rules that apply to the given candidate correlation.
        """
        return [
            rule
            for rule in self.enabled_rules()
            if rule.matches(producer, consumer, kind, confidence)
        ]