"""
------------------------------------------------------------------------------
CorrelAI

Value Classifier

Classifies extracted values into lightweight categories for later analysis.

------------------------------------------------------------------------------
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field

from app.analyzers.value_extractor import ExtractedValue


class ValueCategory(str, Enum):
    AUTH_TOKEN = "auth_token"
    SESSION_ID = "session_id"
    CSRF_TOKEN = "csrf_token"
    TELEMETRY = "telemetry"
    IDENTIFIER = "identifier"
    OTHER = "other"


class ValueClassification(BaseModel):
    """
    Classification result for a single extracted value.
    """

    extracted_value_id: str = Field(..., min_length=1)
    category: ValueCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)
    signals: list[str] = Field(default_factory=list)


class ValueClassifier:
    """
    Lightweight heuristic classifier for extracted values.

    This is intentionally simple for PR 0009. It identifies likely dynamic or
    security-relevant values using names, values, and common token patterns.
    """

    _AUTH_HINTS = (
        "authorization",
        "bearer",
        "access_token",
        "refresh_token",
        "id_token",
        "jwt",
        "token",
        "auth",
    )

    _SESSION_HINTS = (
        "session",
        "sessionid",
        "jsessionid",
        "aspnet_sessionid",
        "phpsessid",
        "sid",
    )

    _CSRF_HINTS = (
        "csrf",
        "xsrf",
        "requestverificationtoken",
        "anti-forgery",
        "antiforgery",
    )

    _TELEMETRY_HINTS = (
        "traceparent",
        "tracestate",
        "traceid",
        "spanid",
        "request-id",
        "requestid",
        "correlation-id",
        "correlationid",
        "x-request-id",
        "x-correlation-id",
    )

    _UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    _JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")

    def classify(self, extracted_value: ExtractedValue) -> ValueClassification:
        """
        Classify a single extracted value.
        """
        text = f"{extracted_value.name} {extracted_value.value}".lower().strip()

        if self._matches(text, self._CSRF_HINTS):
            signals = self._collect_signals(text, self._CSRF_HINTS)
            return self._build(
                extracted_value=extracted_value,
                category=ValueCategory.CSRF_TOKEN,
                confidence=0.98,
                reason="Matched CSRF-related hint(s).",
                signals=signals,
            )

        if self._is_jwt(extracted_value.value) or self._matches(text, self._AUTH_HINTS):
            signals = self._collect_signals(text, self._AUTH_HINTS)
            if self._is_jwt(extracted_value.value):
                signals.append("jwt-pattern")
            return self._build(
                extracted_value=extracted_value,
                category=ValueCategory.AUTH_TOKEN,
                confidence=0.96,
                reason="Matched auth/token-related hint(s).",
                signals=signals,
            )

        if self._matches(text, self._SESSION_HINTS):
            signals = self._collect_signals(text, self._SESSION_HINTS)
            return self._build(
                extracted_value=extracted_value,
                category=ValueCategory.SESSION_ID,
                confidence=0.95,
                reason="Matched session-related hint(s).",
                signals=signals,
            )

        if self._matches(text, self._TELEMETRY_HINTS):
            signals = self._collect_signals(text, self._TELEMETRY_HINTS)
            return self._build(
                extracted_value=extracted_value,
                category=ValueCategory.TELEMETRY,
                confidence=0.93,
                reason="Matched telemetry/correlation hint(s).",
                signals=signals,
            )

        if self._looks_like_identifier(extracted_value.value):
            return self._build(
                extracted_value=extracted_value,
                category=ValueCategory.IDENTIFIER,
                confidence=0.70,
                reason="Value looks like an identifier (UUID, numeric, or hex-style).",
                signals=["identifier-pattern"],
            )

        return self._build(
            extracted_value=extracted_value,
            category=ValueCategory.OTHER,
            confidence=0.50,
            reason="No strong classification signals found.",
            signals=[],
        )

    def classify_many(self, values: list[ExtractedValue]) -> list[ValueClassification]:
        """
        Classify multiple extracted values.
        """
        return [self.classify(value) for value in values]

    def _build(
        self,
        extracted_value: ExtractedValue,
        category: ValueCategory,
        confidence: float,
        reason: str,
        signals: list[str],
    ) -> ValueClassification:
        return ValueClassification(
            extracted_value_id=extracted_value.id,
            category=category,
            confidence=confidence,
            reason=reason,
            signals=signals,
        )

    def _matches(self, text: str, hints: tuple[str, ...]) -> bool:
        return any(hint in text for hint in hints)

    def _collect_signals(self, text: str, hints: tuple[str, ...]) -> list[str]:
        return [hint for hint in hints if hint in text]

    def _is_jwt(self, value: str) -> bool:
        return bool(self._JWT_PATTERN.match(value.strip()))

    def _looks_like_identifier(self, value: str) -> bool:
        normalized = value.strip()
        if not normalized:
            return False

        if self._UUID_PATTERN.match(normalized):
            return True

        if normalized.isdigit() and len(normalized) >= 2:
            return True

        hexish = normalized.replace("-", "")
        if len(hexish) >= 8 and all(ch in "0123456789abcdefABCDEF" for ch in hexish):
            return True

        return False