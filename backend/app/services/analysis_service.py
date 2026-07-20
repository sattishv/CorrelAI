"""
------------------------------------------------------------------------------
CorrelAI

Analysis Service

Coordinates parsing and prepares artifact data for future analysis stages.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from app.ir.transaction import Transaction
from app.services.parser_service import ParserService


class AnalysisService:
    """
    Orchestration layer for artifact analysis.

    This service is intentionally thin for now. It coordinates parser execution
    and returns normalized IR transactions so that future analyzers can consume
    a stable input model.
    """

    def __init__(self, parser_service: ParserService | None = None) -> None:
        self._parser_service = parser_service or ParserService()

    def validate(self, source: Union[str, Path]) -> bool:
        """
        Validate the artifact using the parser service.

        Args:
            source: Path or string path to the artifact.

        Returns:
            True if the artifact is valid.
        """
        return self._parser_service.validate(source)

    def parse(self, source: Union[str, Path]) -> list[Transaction]:
        """
        Parse the artifact into IR transactions.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A list of IR Transaction objects.
        """
        return self._parser_service.parse(source)

    def analyze(self, source: Union[str, Path]) -> dict[str, Any]:
        """
        Prepare a normalized analysis payload for downstream stages.

        For PR 0007, this does not perform advanced correlation or replay
        analysis yet. It simply provides a consistent orchestration boundary.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A dictionary containing the parsed transactions and basic metadata.
        """
        transactions = self.parse(source)

        return {
            "source": str(source),
            "transaction_count": len(transactions),
            "transactions": transactions,
        }