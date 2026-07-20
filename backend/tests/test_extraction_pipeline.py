from app.analyzers import ExtractionPipeline, ValueCategory
from app.analyzers.normalization_result import NormalizationResult
from app.ir.enums import ArtifactType
from app.ir.request import Request
from app.ir.response import Response
from app.ir.transaction import Transaction
from app.models.common import Cookie, Header, Parameter


def build_sample_normalization_result() -> NormalizationResult:
    request = Request(
        id="req-1",
        method="POST",
        url="https://example.com/login",
        headers=[
            Header(name="Authorization", value="Bearer abc.def.ghi"),
            Header(name="X-Request-Id", value="f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
        ],
        cookies=[
            Cookie(name="SessionId", value="session-123"),
        ],
        query_params=[
            Parameter(name="tenantId", value="42"),
        ],
        form_params=[
            Parameter(name="csrfToken", value="token-123"),
        ],
        body='{"csrfToken":"token-123","traceId":"trace-1"}',
        content_type="application/json",
    )

    response = Response(
        id="res-1",
        status_code=200,
        headers=[],
        cookies=[
            Cookie(name="XSRF-TOKEN", value="response-token"),
        ],
        body='{"traceId":"trace-1"}',
        content_type="application/json",
    )

    transaction = Transaction(
        id="tx-1",
        artifact_type=ArtifactType.HAR,
        sequence=1,
        request=request,
        response=response,
        name="login",
    )

    return NormalizationResult(
        artifact_type=ArtifactType.HAR,
        source="sample.har",
        transactions=[transaction],
    )


def test_extraction_pipeline_extracts_and_classifies_values() -> None:
    pipeline = ExtractionPipeline()
    result = pipeline.extract(build_sample_normalization_result())

    assert result.value_count >= 6
    assert result.metadata["classification_summary"]["auth_token"] >= 1
    assert result.metadata["classification_summary"]["session_id"] >= 1
    assert result.metadata["classification_summary"]["csrf_token"] >= 1
    assert result.metadata["classification_summary"]["telemetry"] >= 1

    categories = [item.metadata["classification"]["category"] for item in result.values]
    assert ValueCategory.AUTH_TOKEN.value in categories
    assert ValueCategory.SESSION_ID.value in categories
    assert ValueCategory.CSRF_TOKEN.value in categories
    assert ValueCategory.TELEMETRY.value in categories