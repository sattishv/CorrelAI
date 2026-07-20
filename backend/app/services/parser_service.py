"""
------------------------------------------------------------------------------
CorrelAI

Parser Service

Orchestrates parser selection and parsing of artifacts into IR transactions.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from app.ir.transaction import Transaction
from app.parsers.base_parser import BaseParser
from app.parsers.parser_factory import ParserFactory


class ParserService:
    """
    Service layer for parser orchestration.

    This service keeps the API layer thin by handling parser selection and
    delegating parsing work to the appropriate parser implementation.
    """

    def get_parser(self, source: Union[str, Path]) -> BaseParser:
        """
        Resolve the correct parser for the given artifact source.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A concrete parser instance.
        """
        return ParserFactory.get_parser(source)

    def validate(self, source: Union[str, Path]) -> bool:
        """
        Validate the input artifact using the resolved parser.

        Args:
            source: Path or string path to the artifact.

        Returns:
            True if the artifact is valid.
        """
        parser = self.get_parser(source)
        return parser.validate(source)

    def parse(self, source: Union[str, Path]) -> list[Transaction]:
        """
        Parse the input artifact into IR transactions.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A list of IR Transaction objects.
        """
        parser = self.get_parser(source)
        return parser.parse(source)