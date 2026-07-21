"""
------------------------------------------------------------------------------
CorrelAI

Replay Diagnostics Engine

Analyzes normalized transactions, extracted values, and correlations to
identify replay mismatches and missing dynamic values.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.analyzers.correlation_engine import CorrelationEngine
from app.analyzers.correlation_result import CorrelationLink
from app.analyzers.extraction_pipeline import ExtractionPipeline
from app.analyzers.extraction_result import ExtractionResult
from app.analyzers.normalization_result import NormalizationResult
from app.analyzers.replay_diagnostics_result import (
    ReplayDiagnosticsResult,
    ReplayIssue,
    ReplayIssueKind,
    ReplaySeverity,
    ReplayStatus,
    ReplayStepDiagnostics,
)
from app.analyzers.value_classifier import ValueCategory
from app.analyzers.value_extractor import (
    ExtractedValue,
    ExtractedValueLocation,
    ExtractedValueScope,
)
from app.ir.enums import ArtifactType
from app.ir.transaction import Transaction


class ReplayDiagnosticsEngine:
    """
    Replay diagnostics engine.

    This implementation is intentionally heuristic and explainable. It checks for
    sensitive request values that do not appear to be explained by prior response
    correlations, which is a common signal of replay failure.
    """

    def __init__(
        self,
        extraction_pipeline: ExtractionPipeline | None = None,
        correlation_engine: CorrelationEngine | None = None,
    ) -> None:
        self._extraction_pipeline = extraction_pipeline or ExtractionPipeline()
        self._correlation_engine = correlation_engine or CorrelationEngine(
            extraction_pipeline=self._extraction_pipeline
        )

    def diagnose(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> ReplayDiagnosticsResult:
        """
        Diagnose likely replay issues from a normalized source.

        Args:
            source: Normalized result, extraction result, or transaction iterable.

        Returns:
            ReplayDiagnosticsResult containing step-level and aggregate issues.
        """
        source_name, normalization_result, extraction_result = self._resolve_source(source)
        correlation_result = self._correlation_engine.correlate(normalization_result)

        values_by_transaction = defaultdict(list)
        for value in extraction_result.values:
            values_by_transaction[value.transaction_id].append(value)

        incoming_links_by_transaction: dict[str, list[CorrelationLink]] = defaultdict(list)
        for link in correlation_result.links:
            incoming_links_by_transaction[link.target_transaction_id].append(link)

        steps: list[ReplayStepDiagnostics] = []
        all_issues: list[ReplayIssue] = []

        for transaction in normalization_result.transactions:
            step_values = values_by_transaction.get(transaction.id, [])
            step_links = incoming_links_by_transaction.get(transaction.id, [])
            step_issues: list[ReplayIssue] = []

            sensitive_values = [
                value
                for value in step_values
                if value.scope == ExtractedValueScope.REQUEST
                and self._is_sensitive_value(value)
            ]

            if sensitive_values and not step_links:
                for value in sensitive_values:
                    issue = self._build_missing_value_issue(transaction, value)
                    step_issues.append(issue)
                    all_issues.append(issue)

            elif sensitive_values and step_links:
                # If we have incoming links, but the sensitive value still looks
                # suspicious, keep the step in PARTIAL status so later PRs can
                # refine the heuristics.
                for value in sensitive_values:
                    if not self._has_matching_incoming_link(value, step_links):
                        issue = self._build_missing_value_issue(transaction, value)
                        step_issues.append(issue)
                        all_issues.append(issue)

            step_status = self._derive_step_status(step_issues)

            steps.append(
                ReplayStepDiagnostics(
                    transaction_id=transaction.id,
                    request_name=self._transaction_label(transaction),
                    status=step_status,
                    issues=step_issues,
                    metadata={
                        "sensitive_value_count": len(sensitive_values),
                        "incoming_link_count": len(step_links),
                    },
                )
            )

        result_status = self._derive_result_status(steps, all_issues)
        warnings: list[str] = []

        if not normalization_result.transactions:
            warnings.append("No transactions were available for replay diagnostics.")
        if not extraction_result.values:
            warnings.append("No extracted values were available for replay diagnostics.")
        if not correlation_result.links:
            warnings.append("No correlation links were available for replay diagnostics.")

        return ReplayDiagnosticsResult(
            source=source_name,
            status=result_status,
            steps=steps,
            issues=all_issues,
            warnings=warnings,
            metadata={
                "artifact_type": normalization_result.artifact_type.value,
                "transaction_count": len(normalization_result.transactions),
                "value_count": extraction_result.value_count,
                "correlation_count": correlation_result.correlation_count,
            },
        )

    def summarize(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> dict[str, Any]:
        """
        Return a lightweight summary suitable for API responses or previews.
        """
        result = self.diagnose(source)

        return {
            "id": result.id,
            "source": result.source,
            "generated_at": result.generated_at.isoformat(),
            "status": result.status.value,
            "step_count": result.step_count,
            "issue_count": result.issue_count,
            "warnings": result.warnings,
            "metadata": result.metadata,
        }

    def _resolve_source(
        self,
        source: NormalizationResult | ExtractionResult | Iterable[Transaction],
    ) -> tuple[str, NormalizationResult, ExtractionResult]:
        """
        Resolve supported inputs into a source name, normalization result, and extraction result.
        """
        if isinstance(source, ExtractionResult):
            normalization_result = self._wrap_extraction_result(source)
            return source.source, normalization_result, source

        if isinstance(source, NormalizationResult):
            extraction_result = self._extraction_pipeline.extract(source)
            return source.source, source, extraction_result

        transactions = list(source)
        normalization_result = NormalizationResult(
            artifact_type=ArtifactType.TRACE,
            source="memory",
            transactions=transactions,
        )
        extraction_result = self._extraction_pipeline.extract(normalization_result)
        return "memory", normalization_result, extraction_result

    def _wrap_extraction_result(self, result: ExtractionResult) -> NormalizationResult:
        """
        Rebuild a normalization result from an extraction result when needed.
        """
        transactions: list[Transaction] = []
        return NormalizationResult(
            artifact_type=ArtifactType.TRACE,
            source=result.source,
            transactions=transactions,
        )

    def _is_sensitive_value(self, value: ExtractedValue) -> bool:
        """
        Determine whether an extracted value is likely to participate in replay issues.
        """
        category = self._get_category(value)

        return category in {
            ValueCategory.AUTH_TOKEN.value,
            ValueCategory.SESSION_ID.value,
            ValueCategory.CSRF_TOKEN.value,
        }

    def _has_matching_incoming_link(
        self,
        value: ExtractedValue,
        links: list[CorrelationLink],
    ) -> bool:
        """
        Determine whether the current request value appears to be explained by an incoming correlation.
        """
        value_name = value.name.strip().lower()
        value_text = value.value.strip()

        for link in links:
            if link.matched_name.strip().lower() == value_name:
                return True

            if link.matched_value.strip() == value_text:
                return True

        return False

    def _build_missing_value_issue(
        self,
        transaction: Transaction,
        value: ExtractedValue,
    ) -> ReplayIssue:
        """
        Build a replay issue for an unexplained sensitive request value.
        """
        kind = self._map_location_to_issue_kind(value.location)
        severity = self._map_category_to_severity(self._get_category(value))

        return ReplayIssue(
            kind=kind,
            severity=severity,
            transaction_id=transaction.id,
            request_name=self._transaction_label(transaction),
            field_name=value.name,
            expected_value="value produced by an earlier response",
            observed_value=value.value,
            message=(
                f"Sensitive request value '{value.name}' was not explained by a "
                f"prior correlation link."
            ),
            confidence=0.90,
            metadata={
                "location": value.location.value,
                "scope": value.scope.value,
                "category": self._get_category(value),
            },
        )

    def _map_location_to_issue_kind(self, location: ExtractedValueLocation) -> ReplayIssueKind:
        """
        Map extracted value location to a replay issue kind.
        """
        if location == ExtractedValueLocation.HEADER:
            return ReplayIssueKind.MISSING_TOKEN
        if location == ExtractedValueLocation.COOKIE:
            return ReplayIssueKind.COOKIE_MISMATCH
        if location in {
            ExtractedValueLocation.QUERY_PARAM,
            ExtractedValueLocation.FORM_PARAM,
        }:
            return ReplayIssueKind.PARAMETER_MISMATCH
        if location in {
            ExtractedValueLocation.BODY,
            ExtractedValueLocation.BODY_JSON,
        }:
            return ReplayIssueKind.BODY_MISMATCH

        return ReplayIssueKind.UNKNOWN

    def _map_category_to_severity(self, category: str) -> ReplaySeverity:
        """
        Map a value classification category to issue severity.
        """
        category = category.lower()

        if category in {ValueCategory.AUTH_TOKEN.value, ValueCategory.CSRF_TOKEN.value}:
            return ReplaySeverity.CRITICAL

        if category == ValueCategory.SESSION_ID.value:
            return ReplaySeverity.HIGH

        return ReplaySeverity.MEDIUM

    def _derive_step_status(self, issues: list[ReplayIssue]) -> ReplayStatus:
        """
        Derive a step status from its issues.
        """
        if not issues:
            return ReplayStatus.PASS

        severities = {issue.severity for issue in issues}
        if ReplaySeverity.CRITICAL in severities or ReplaySeverity.HIGH in severities:
            return ReplayStatus.FAIL

        return ReplayStatus.PARTIAL

    def _derive_result_status(
        self,
        steps: list[ReplayStepDiagnostics],
        issues: list[ReplayIssue],
    ) -> ReplayStatus:
        """
        Derive overall replay status from step diagnostics.
        """
        if not steps:
            return ReplayStatus.UNKNOWN

        if not issues:
            return ReplayStatus.PASS

        statuses = {step.status for step in steps}
        if ReplayStatus.FAIL in statuses:
            return ReplayStatus.FAIL

        if ReplayStatus.PARTIAL in statuses:
            return ReplayStatus.PARTIAL

        return ReplayStatus.UNKNOWN

    def _transaction_label(self, transaction: Transaction) -> str:
        """
        Build a human-readable transaction label.
        """
        if transaction.name:
            return transaction.name

        method = transaction.request.method.strip()
        url = transaction.request.url.strip()

        if method and url:
            return f"{method} {url}"

        return f"Transaction {transaction.sequence or transaction.id}"

    def _get_category(self, value: ExtractedValue) -> str:
        """
        Read the classification category from an extracted value.
        """
        classification = value.metadata.get("classification", {})
        return str(classification.get("category", "")).lower().strip()