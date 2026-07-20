"""
------------------------------------------------------------------------------
CorrelAI

Value Extractor

Extracts candidate values from normalized IR transactions for later analysis.

------------------------------------------------------------------------------
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Iterable, List
from uuid import uuid4

from pydantic import BaseModel, Field

from app.ir.transaction import Transaction


class ExtractedValueScope(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"


class ExtractedValueLocation(str, Enum):
    HEADER = "header"
    COOKIE = "cookie"
    QUERY_PARAM = "query_param"
    FORM_PARAM = "form_param"
    BODY = "body"
    BODY_JSON = "body_json"


class ExtractedValue(BaseModel):
    """
    Normalized value extracted from a transaction.

    This is the basic unit used by later correlation, dependency, and replay
    analysis stages.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_id: str = Field(..., min_length=1)
    scope: ExtractedValueScope
    location: ExtractedValueLocation
    name: str = Field(..., min_length=1)
    value: str = Field(default="", min_length=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValueExtractor:
    """
    Extracts candidate values from a normalized transaction.

    For PR 0009, the extractor focuses on structural sources:
    - headers
    - cookies
    - query parameters
    - form parameters
    - basic body candidates

    Deeper token classification and correlation will come in later PRs.
    """

    def extract(self, transaction: Transaction) -> list[ExtractedValue]:
        """
        Extract all candidate values from a single transaction.

        Args:
            transaction: Normalized IR transaction.

        Returns:
            List of extracted values.
        """
        extracted: list[ExtractedValue] = []

        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.REQUEST,
                location=ExtractedValueLocation.HEADER,
                items=transaction.request.headers,
            )
        )
        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.REQUEST,
                location=ExtractedValueLocation.COOKIE,
                items=transaction.request.cookies,
            )
        )
        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.REQUEST,
                location=ExtractedValueLocation.QUERY_PARAM,
                items=transaction.request.query_params,
            )
        )
        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.REQUEST,
                location=ExtractedValueLocation.FORM_PARAM,
                items=transaction.request.form_params,
            )
        )

        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.RESPONSE,
                location=ExtractedValueLocation.HEADER,
                items=transaction.response.headers,
            )
        )
        extracted.extend(
            self._extract_pairs(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.RESPONSE,
                location=ExtractedValueLocation.COOKIE,
                items=transaction.response.cookies,
            )
        )

        extracted.extend(self._extract_body_candidates(transaction))

        return extracted

    def extract_many(self, transactions: Iterable[Transaction]) -> list[ExtractedValue]:
        """
        Extract values from multiple transactions.

        Args:
            transactions: Iterable of normalized IR transactions.

        Returns:
            Combined list of extracted values.
        """
        extracted: list[ExtractedValue] = []
        for transaction in transactions:
            extracted.extend(self.extract(transaction))
        return extracted

    def _extract_pairs(
        self,
        transaction_id: str,
        scope: ExtractedValueScope,
        location: ExtractedValueLocation,
        items: Iterable[Any],
    ) -> list[ExtractedValue]:
        """
        Convert name/value pairs into extracted values.
        """
        results: list[ExtractedValue] = []

        for item in items:
            name = getattr(item, "name", "")
            value = getattr(item, "value", "")

            if not name and not value:
                continue

            results.append(
                ExtractedValue(
                    transaction_id=transaction_id,
                    scope=scope,
                    location=location,
                    name=str(name),
                    value=str(value),
                    metadata={
                        "source_location": location.value,
                    },
                )
            )

        return results

    def _extract_body_candidates(self, transaction: Transaction) -> list[ExtractedValue]:
        """
        Extract simple candidates from request/response bodies.

        For PR 0009, we only attempt a lightweight JSON parse. If parsing fails,
        the body is ignored for now.
        """
        results: list[ExtractedValue] = []

        results.extend(
            self._extract_json_body(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.REQUEST,
                body=transaction.request.body,
            )
        )
        results.extend(
            self._extract_json_body(
                transaction_id=transaction.id,
                scope=ExtractedValueScope.RESPONSE,
                body=transaction.response.body,
            )
        )

        return results

    def _extract_json_body(
        self,
        transaction_id: str,
        scope: ExtractedValueScope,
        body: str | None,
    ) -> list[ExtractedValue]:
        """
        Attempt to extract scalar values from a JSON body.
        """
        if not body:
            return []

        body_text = body.strip()
        if not body_text:
            return []

        if not body_text.startswith("{") and not body_text.startswith("["):
            return []

        try:
            parsed = json.loads(body_text)
        except json.JSONDecodeError:
            return []

        flattened: list[tuple[str, str]] = []
        self._flatten_json(parsed, flattened, prefix="")

        return [
            ExtractedValue(
                transaction_id=transaction_id,
                scope=scope,
                location=ExtractedValueLocation.BODY_JSON,
                name=name,
                value=value,
                metadata={
                    "source_location": ExtractedValueLocation.BODY_JSON.value,
                    "json_path": name,
                },
            )
            for name, value in flattened
            if name or value
        ]

    def _flatten_json(
        self,
        value: Any,
        output: list[tuple[str, str]],
        prefix: str,
    ) -> None:
        """
        Flatten JSON structures into dotted key/value pairs.

        Only scalar values are collected for now.
        """
        if isinstance(value, dict):
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                self._flatten_json(item, output, next_prefix)
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                next_prefix = f"{prefix}[{index}]"
                self._flatten_json(item, output, next_prefix)
            return

        output.append((prefix, "" if value is None else str(value)))