"""Deterministic validators.

Each validator returns every issue it finds instead of stopping at the first,
so a result can carry the full list into review and rule tracing.
"""

from collections.abc import Iterable

from app.contracts.models import (
    AnnotationResult,
    AnswerBox,
    BoundingBox,
    Issue,
    Page,
    QuestionNode,
    ResultStatus,
    Severity,
)


def validate_page_bounds(
    pages: Iterable[Page],
    questions: Iterable[QuestionNode],
    answers: Iterable[AnswerBox] = (),
) -> list[Issue]:
    issues: list[Issue] = []
    by_id: dict[str, Page] = {}
    for page in pages:
        if page.id in by_id:
            issues.append(
                Issue(code="DUPLICATE_PAGE_ID", message=f"page {page.id} repeats", refs=[page.id])
            )
            continue
        by_id[page.id] = page

    owned_boxes: list[tuple[str, BoundingBox]] = [(q.id, q.bbox) for q in questions]
    owned_boxes += [(a.id, a.bbox) for a in answers if a.bbox is not None]

    for owner_id, box in owned_boxes:
        page = by_id.get(box.page_id)
        if page is None:
            issues.append(
                Issue(
                    code="PAGE_NOT_FOUND",
                    message=f"{owner_id} references unknown page {box.page_id}",
                    refs=[owner_id],
                )
            )
        elif box.x2 > page.width or box.y2 > page.height:
            issues.append(
                Issue(
                    code="COORDINATE_OUT_OF_BOUNDS",
                    message=f"{owner_id} box exceeds page {page.id} ({page.width}x{page.height})",
                    refs=[owner_id],
                )
            )
    return issues


def validate_question_hierarchy(questions: Iterable[QuestionNode]) -> list[Issue]:
    issues: list[Issue] = []
    by_id: dict[str, QuestionNode] = {}
    for question in questions:
        if question.id in by_id:
            issues.append(
                Issue(
                    code="DUPLICATE_QUESTION_ID",
                    message=f"question {question.id} repeats",
                    refs=[question.id],
                )
            )
            continue
        by_id[question.id] = question

    for question in by_id.values():
        # Self-parents are reported as cycles below; a box always contains itself.
        if question.parent_id is None or question.parent_id == question.id:
            continue
        parent = by_id.get(question.parent_id)
        if parent is None:
            issues.append(
                Issue(
                    code="PARENT_NOT_FOUND",
                    message=f"question {question.id} references {question.parent_id}",
                    refs=[question.id, question.parent_id],
                )
            )
        elif question.bbox.page_id != parent.bbox.page_id:
            issues.append(
                Issue(
                    code="PARENT_PAGE_MISMATCH",
                    message=f"question {question.id} and parent {parent.id} are on different pages",
                    refs=[question.id, parent.id],
                )
            )
        elif not _contains(parent.bbox, question.bbox):
            issues.append(
                Issue(
                    code="CHILD_OUTSIDE_PARENT",
                    message=f"question {question.id} is outside parent {parent.id}",
                    refs=[question.id, parent.id],
                )
            )

    issues += _parent_cycles(by_id)
    return issues


def validate_answer_bindings(
    questions: Iterable[QuestionNode], answers: Iterable[AnswerBox]
) -> list[Issue]:
    issues: list[Issue] = []
    question_ids = {question.id for question in questions}
    seen: set[str] = set()
    for answer in answers:
        if answer.id in seen:
            issues.append(
                Issue(
                    code="DUPLICATE_ANSWER_ID",
                    message=f"answer {answer.id} repeats",
                    refs=[answer.id],
                )
            )
            continue
        seen.add(answer.id)
        if answer.question_id not in question_ids:
            issues.append(
                Issue(
                    code="QUESTION_NOT_FOUND",
                    message=f"answer {answer.id} references {answer.question_id}",
                    refs=[answer.id, answer.question_id],
                )
            )
    return issues


def validate_annotation(
    pages: Iterable[Page],
    questions: Iterable[QuestionNode],
    answers: Iterable[AnswerBox] = (),
    *,
    confidence: float | None = None,
) -> AnnotationResult:
    """Run every validator and build a result whose status follows the issues."""
    pages, questions, answers = list(pages), list(questions), list(answers)
    issues = (
        validate_page_bounds(pages, questions, answers)
        + validate_question_hierarchy(questions)
        + validate_answer_bindings(questions, answers)
    )
    has_blocking = any(issue.severity is Severity.BLOCKING for issue in issues)
    return AnnotationResult(
        pages=pages,
        questions=questions,
        answers=answers,
        issues=issues,
        status=ResultStatus.NEEDS_REVIEW if has_blocking else ResultStatus.PASSED,
        confidence=confidence,
    )


def _parent_cycles(by_id: dict[str, QuestionNode]) -> list[Issue]:
    issues: list[Issue] = []
    reported: set[frozenset[str]] = set()
    for start in by_id.values():
        path = [start.id]
        current = start
        while current.parent_id is not None and current.parent_id in by_id:
            if current.parent_id in path:
                members = frozenset(path[path.index(current.parent_id):])
                if members not in reported:
                    reported.add(members)
                    refs = sorted(members)
                    issues.append(
                        Issue(
                            code="PARENT_CYCLE",
                            message=f"questions {', '.join(refs)} form a parent cycle",
                            refs=refs,
                        )
                    )
                break
            path.append(current.parent_id)
            current = by_id[current.parent_id]
    return issues


def _contains(parent: BoundingBox, child: BoundingBox) -> bool:
    return (
        parent.x1 <= child.x1
        and parent.y1 <= child.y1
        and parent.x2 >= child.x2
        and parent.y2 >= child.y2
    )
