"""
------------------------------------------------------------------------------
CorrelAI

IR Enums

Shared enums used across the Intermediate Representation.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from enum import Enum


class ArtifactType(str, Enum):
    HAR = "har"
    JMX = "jmx"
    JTL = "jtl"
    POSTMAN = "postman"
    TRACE = "trace"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls}