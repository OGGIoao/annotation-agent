from collections.abc import Iterable

from app.contracts.models import AnswerBox, BoundingBox, QuestionNode


class ValidationIssue(ValueError):
    """A deterministic validation failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def validate_page_bounds(
    boxes: Iterable[BoundingBox], *, page_width: float, page_height: float
) -> None:
    for box in boxes:
        if box.x2 > page_width or box.y2 > page_height:
            raise ValidationIssue(
                "COORDINATE_OUT_OF_BOUNDS",
                f"{box.page_id} box exceeds {page_width}x{page_height}",
            )


def validate_question_hierarchy(questions: Iterable[QuestionNode]) -> None:
    by_id = {question.id: question for question in questions}
    for question in by_id.values():
        if question.parent_id is None:
            continue
        parent = by_id.get(question.parent_id)
        if parent is None:
            raise ValidationIssue(
                "PARENT_NOT_FOUND",
                f"question {question.id} references {question.parent_id}",
            )
        if question.bbox.page_id != parent.bbox.page_id:
            raise ValidationIssue(
                "PARENT_PAGE_MISMATCH",
                f"question {question.id} and parent {parent.id} are on different pages",
            )
        if not _contains(parent.bbox, question.bbox):
            raise ValidationIssue(
                "CHILD_OUTSIDE_PARENT",
                f"question {question.id} is outside parent {parent.id}",
            )


def validate_answer_bindings(
    questions: Iterable[QuestionNode], answers: Iterable[AnswerBox]
) -> None:
    question_ids = {question.id for question in questions}
    seen: set[str] = set()
    for answer in answers:
        if answer.question_id not in question_ids:
            raise ValidationIssue(
                "QUESTION_NOT_FOUND",
                f"answer {answer.id} references {answer.question_id}",
            )
        if answer.id in seen:
            raise ValidationIssue("DUPLICATE_ANSWER_ID", f"answer {answer.id} repeats")
        seen.add(answer.id)


def _contains(parent: BoundingBox, child: BoundingBox) -> bool:
    return (
        parent.x1 <= child.x1
        and parent.y1 <= child.y1
        and parent.x2 >= child.x2
        and parent.y2 >= child.y2
    )
