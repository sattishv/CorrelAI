"""
------------------------------------------------------------------------------
CorrelAI

Parser Exceptions

Custom exception types used by artifact parsers.

------------------------------------------------------------------------------
"""


class ParserError(Exception):
    """Base class for all parser-related errors."""


class ParserValidationError(ParserError):
    """Raised when an artifact fails parser validation."""


class InvalidArtifactError(ParserError):
    """Raised when the provided artifact is malformed or unsupported."""


class UnsupportedVersionError(ParserError):
    """Raised when the artifact version is not supported."""


class InvalidHarFileError(InvalidArtifactError):
    """Raised when a HAR file is structurally invalid."""