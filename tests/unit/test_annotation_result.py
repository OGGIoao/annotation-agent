from pydantic import ValidationError
import pytest

from app.contracts.models import (
    AnnotationResult,
    Issue,
    Page,
    ResultStatus,
    Severity,
)


def blocking() -> Issue:
    return Issue(code="PARENT_NOT_FOUND", message="missing parent", refs=["1-1"])


def warning() -> Issue:
    return Issue(code="LOW_CONFIDENCE", severity=Severity.WARNING, message="check")


def result(**overrides) -> AnnotationResult:
    fields = {
        "pages": [Page(id="p1", width=100, height=100)],
        "questions": [],
        "status": ResultStatus.PASSED,
    }
    return AnnotationResult(**{**fields, **overrides})


def test_issue_defaults_to_blocking() -> None:
    assert blocking().severity is Severity.BLOCKING


def test_result_cannot_pass_with_blocking_issue() -> None:
    with pytest.raises(ValidationError):
        result(issues=[blocking()], status=ResultStatus.PASSED)


def test_result_cannot_need_review_without_blocking_issue() -> None:
    with pytest.raises(ValidationError):
        result(issues=[warning()], status=ResultStatus.NEEDS_REVIEW)


def test_result_can_pass_with_warnings_only() -> None:
    assert result(issues=[warning()]).status is ResultStatus.PASSED


def test_result_with_blocking_issue_needs_review() -> None:
    needs_review = result(issues=[blocking()], status=ResultStatus.NEEDS_REVIEW)
    assert needs_review.status is ResultStatus.NEEDS_REVIEW


def test_result_requires_at_least_one_page() -> None:
    with pytest.raises(ValidationError):
        result(pages=[])


@pytest.mark.parametrize("confidence", [-0.1, 1.1, float("nan")])
def test_result_rejects_invalid_confidence(confidence: float) -> None:
    with pytest.raises(ValidationError):
        result(confidence=confidence)


@pytest.mark.parametrize("width", [0, -1, float("inf")])
def test_page_requires_positive_finite_size(width: float) -> None:
    with pytest.raises(ValidationError):
        Page(id="p1", width=width, height=100)
