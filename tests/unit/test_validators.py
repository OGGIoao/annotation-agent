import pytest

from app.contracts.models import BoundingBox, LineType, QuestionNode, Subject, QuestionType
from app.rules.validators import (
    ValidationIssue,
    validate_answer_bindings,
    validate_page_bounds,
    validate_question_hierarchy,
)


def make_box(x1=0, y1=0, x2=100, y2=100, page_id="p1"):
    return BoundingBox(page_id=page_id, x1=x1, y1=y1, x2=x2, y2=y2)


def question(question_id, bbox, parent_id=None):
    return QuestionNode(
        id=question_id,
        bbox=bbox,
        subject=Subject.MATH,
        types=[QuestionType.CHOICE],
        line_type=LineType.SOLID,
        parent_id=parent_id,
    )


def test_page_bounds_reject_box_outside_page():
    with pytest.raises(ValidationIssue, match="COORDINATE_OUT_OF_BOUNDS"):
        validate_page_bounds([make_box(x2=101)], page_width=100, page_height=100)


def test_question_hierarchy_rejects_missing_parent():
    with pytest.raises(ValidationIssue, match="PARENT_NOT_FOUND"):
        validate_question_hierarchy([question("1-1", make_box(), parent_id="1")])


def test_question_hierarchy_rejects_child_outside_parent():
    questions = [question("1", make_box()), question("1-1", make_box(x1=90, x2=120), "1")]
    with pytest.raises(ValidationIssue, match="CHILD_OUTSIDE_PARENT"):
        validate_question_hierarchy(questions)


def test_answer_binding_rejects_unknown_question():
    from app.contracts.models import AnswerBox, AnswerMode, Closedness

    answer = AnswerBox(
        id="1-答1",
        question_id="missing",
        bbox=make_box(),
        text="A",
        mode=AnswerMode.TEXT,
        closedness=Closedness.CLOSED,
    )
    with pytest.raises(ValidationIssue, match="QUESTION_NOT_FOUND"):
        validate_answer_bindings([], [answer])
