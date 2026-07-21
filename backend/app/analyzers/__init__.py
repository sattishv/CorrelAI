"""
------------------------------------------------------------------------------
CorrelAI

Analyzers Package

Exports normalization, extraction, and correlation components.

------------------------------------------------------------------------------
"""

from app.analyzers.analyzer_factory import AnalyzerFactory
from app.analyzers.correlation_engine import CorrelationEngine
from app.analyzers.correlation_result import (
    CorrelationEvidence,
    CorrelationKind,
    CorrelationLink,
    CorrelationResult,
)
from app.analyzers.correlation_rules import (
    CorrelationMatchMode,
    CorrelationRule,
    CorrelationRuleSet,
)
from app.analyzers.extraction_pipeline import ExtractionPipeline
from app.analyzers.extraction_result import ExtractionResult
from app.analyzers.normalization_pipeline import NormalizationPipeline
from app.analyzers.normalization_result import NormalizationResult
from app.analyzers.value_classifier import (
    ValueCategory,
    ValueClassification,
    ValueClassifier,
)
from app.analyzers.value_extractor import (
    ExtractedValue,
    ExtractedValueLocation,
    ExtractedValueScope,
    ValueExtractor,
)

__all__ = [
    "AnalyzerFactory",
    "CorrelationEngine",
    "CorrelationEvidence",
    "CorrelationKind",
    "CorrelationLink",
    "CorrelationResult",
    "CorrelationMatchMode",
    "CorrelationRule",
    "CorrelationRuleSet",
    "ExtractionPipeline",
    "ExtractionResult",
    "NormalizationPipeline",
    "NormalizationResult",
    "ValueCategory",
    "ValueClassification",
    "ValueClassifier",
    "ExtractedValue",
    "ExtractedValueLocation",
    "ExtractedValueScope",
    "ValueExtractor",
]