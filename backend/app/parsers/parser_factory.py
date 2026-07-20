"""
------------------------------------------------------------------------------
CorrelAI

Parser Factory

Selects the correct parser implementation for a given artifact source.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from app.parsers.base_parser import BaseParser
from app.parsers.exceptions import UnsupportedVersionError
from app.parsers.har_parser import HarParser


class ParserFactory:
    """
    Factory for resolving the appropriate parser for an input artifact.
    """

    @staticmethod
    def get_parser(source: Union[str, Path]) -> BaseParser:
        """
        Return the correct parser for the given source.

        Args:
            source: Path or string path to the artifact.

        Returns:
            A parser instance.

        Raises:
            UnsupportedVersionError: If no parser exists for the artifact type.
        """
        path = Path(source)
        suffix = path.suffix.lower()

        if suffix == ".har":
            return HarParser()

        raise UnsupportedVersionError(f"No parser available for artifact type: {suffix}")