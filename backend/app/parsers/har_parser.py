"""
------------------------------------------------------------------------------
CorrelAI

HAR Parser

Parses HAR 1.2 artifacts into the CorrelAI Intermediate Representation (IR).

------------------------------------------------------------------------------
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.ir.enums import ArtifactType, HttpMethod
from app.ir.request import Request
from app.ir.response import Response
from app.ir.transaction import Transaction
from app.parsers.base_parser import BaseParser
from app.parsers.exceptions import InvalidHarFileError, ParserValidationError, UnsupportedVersionError


class HarParser(BaseParser):
    """
    Parse HAR files into IR transactions.
    """

    def validate(self, source: Path | str) -> bool:
        """
        Validate that the source is a readable HAR file with a valid structure.
        """
        path = Path(source)

        if not path.exists():
            raise ParserValidationError(f"HAR file does not exist: {path}")

        if not path.is_file():
            raise ParserValidationError(f"Source is not a file: {path}")

        if path.suffix.lower() != ".har":
            raise UnsupportedVersionError(f"Unsupported file extension: {path.suffix}")

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise InvalidHarFileError(f"Invalid HAR JSON: {exc}") from exc

        if "log" not in payload:
            raise InvalidHarFileError("HAR file is missing required 'log' object")

        log = payload["log"]
        if not isinstance(log, dict):
            raise InvalidHarFileError("'log' must be an object")

        if log.get("version") not in {"1.1", "1.2"}:
            raise UnsupportedVersionError(
                f"Unsupported HAR version: {log.get('version')}"
            )

        if "entries" not in log or not isinstance(log["entries"], list):
            raise InvalidHarFileError("HAR log must contain an 'entries' array")

        return True

    def parse(self, source: Path | str) -> list[Transaction]:
        """
        Parse the HAR file and return IR transactions.
        """
        self.validate(source)

        path = Path(source)
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        log = payload["log"]
        entries = log.get("entries", [])

        transactions: list[Transaction] = []
        for index, entry in enumerate(entries, start=1):
            transactions.append(self._parse_entry(entry, index))

        return transactions

    def _parse_entry(self, entry: dict[str, Any], index: int) -> Transaction:
        """
        Convert a single HAR entry into an IR Transaction.
        """
        request_data = entry.get("request", {})
        response_data = entry.get("response", {})

        request = self._parse_request(request_data, index)
        response = self._parse_response(response_data)

        return Transaction(
            id=str(uuid4()),
            artifact_type=ArtifactType.HAR,
            sequence=index,
            request=request,
            response=response,
            source="har",
            captured_at=self._parse_timestamp(entry.get("startedDateTime")),
            metadata={
                "har_entry_index": index,
                "pageref": entry.get("pageref"),
            },
        )

    def _parse_request(self, data: dict[str, Any], index: int) -> Request:
        """
        Convert HAR request data into an IR Request.
        """
        headers = [
            {"name": h.get("name", ""), "value": h.get("value", "")}
            for h in data.get("headers", [])
            if isinstance(h, dict)
        ]

        cookies = [
            {"name": c.get("name", ""), "value": c.get("value", "")}
            for c in data.get("cookies", [])
            if isinstance(c, dict)
        ]

        query_params = [
            {"name": p.get("name", ""), "value": p.get("value", "")}
            for p in data.get("queryString", [])
            if isinstance(p, dict)
        ]

        post_data = data.get("postData", {}) if isinstance(data.get("postData"), dict) else {}
        form_params = [
            {"name": p.get("name", ""), "value": p.get("value", "")}
            for p in post_data.get("params", [])
            if isinstance(p, dict)
        ]

        body = post_data.get("text")
        mime_type = post_data.get("mimeType") or data.get("mimeType")

        method = data.get("method", "GET").upper()
        if method not in HttpMethod.values():
            method = "UNKNOWN"

        return Request(
            id=str(uuid4()),
            artifact_type=ArtifactType.HAR,
            sequence=index,
            method=method,
            url=data.get("url", ""),
            http_version=data.get("httpVersion"),
            headers=headers,
            cookies=cookies,
            query_params=query_params,
            form_params=form_params,
            body=body,
            content_type=mime_type,
            metadata={
                "har_method": data.get("method"),
                "har_method_original": data.get("method"),
            },
        )

    def _parse_response(self, data: dict[str, Any]) -> Response:
        """
        Convert HAR response data into an IR Response.
        """
        headers = [
            {"name": h.get("name", ""), "value": h.get("value", "")}
            for h in data.get("headers", [])
            if isinstance(h, dict)
        ]

        cookies = [
            {"name": c.get("name", ""), "value": c.get("value", "")}
            for c in data.get("cookies", [])
            if isinstance(c, dict)
        ]

        content = data.get("content", {}) if isinstance(data.get("content"), dict) else {}

        status = int(data.get("status", 0))
        status_text = data.get("statusText")
        http_version = data.get("httpVersion")
        body = content.get("text")
        mime_type = content.get("mimeType")
        size = content.get("size")

        redirect_url = None
        for header in headers:
            if header["name"].lower() == "location":
                redirect_url = header["value"]
                break

        return Response(
            id=str(uuid4()),
            artifact_type=ArtifactType.HAR,
            status_code=status,
            status_text=status_text,
            http_version=http_version,
            headers=headers,
            cookies=cookies,
            body=body,
            content_type=mime_type,
            size_bytes=size if isinstance(size, int) else None,
            redirect_url=redirect_url,
            is_redirect=300 <= status < 400,
            metadata={
                "har_status_text": status_text,
                "har_encoding": content.get("encoding"),
            },
        )

    def _parse_timestamp(self, value: Any) -> datetime:
        """
        Parse HAR timestamp to a timezone-aware datetime.
        """
        if not isinstance(value, str) or not value:
            return datetime.now(timezone.utc)

        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now(timezone.utc)