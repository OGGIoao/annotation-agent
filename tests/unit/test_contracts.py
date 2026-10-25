from pydantic import ValidationError
import pytest

from app.contracts.models import (
    AnswerBox,
    AnswerMode,
    BoundingBox,
    Closedness,
    LineType,
    QuestionNode,
    QuestionType,
    Subject,
)


def box(page_id: str = "p001") -> BoundingBox:
    return BoundingBox(page_id=page_id, x1=10, y1=20, x2=100, y2=120)


def test_bounding_box_requires_positive_area() -> None:
    with pytest.raises(ValidationError):
        BoundingBox(page_id="p001", x1=100, y1=20, x2=10, y2=120)


def test_question_node_requires_a_question_type() -> None:
    with pytest.raises(ValidationError):
        QuestionNode(
            id="1",
            bbox=box(),
            subject=Subject.MATH,
            types=[],
            line_type=LineType.SOLID,
        )


def test_answer_box_can_represent_a_text_answer() -> None:
    answer = AnswerBox(
        id="1-答1",
        question_id="1",
        bbox=box(),
        text="A",
        mode=AnswerMode.TEXT,
        closedness=Closedness.CLOSED,
    )

    assert answer.question_id == "1"
    assert answer.mode is AnswerMode.TEXT
    assert answer.closedness is Closedness.CLOSED


def test_question_node_accepts_multiple_types_for_compound_questions() -> None:
    question = QuestionNode(
        id="2",
        bbox=box(),
        subject=Subject.MATH,
        types=[QuestionType.READING, QuestionType.CHOICE],
        line_type=LineType.SOLID,
    )

    assert question.types == [QuestionType.READING, QuestionType.CHOICE]


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_bounding_box_rejects_non_finite_coordinates(value: float) -> None:
    with pytest.raises(ValidationError):
        BoundingBox(page_id="p001", x1=0, y1=0, x2=value, y2=120)
