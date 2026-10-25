from app.contracts.models import (
    AnswerBox,
    AnswerMode,
    BoundingBox,
    Closedness,
    Issue,
    LineType,
    Page,
    QuestionNode,
    QuestionType,
    ResultStatus,
    Severity,
    Subject,
)
from app.rules.validators import (
    validate_annotation,
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


def answer(answer_id, question_id, bbox=None, mode=AnswerMode.TEXT):
    return AnswerBox(
        id=answer_id,
        question_id=question_id,
        bbox=bbox if bbox is not None or mode is AnswerMode.BLANK else make_box(),
        text="A",
        mode=mode,
        closedness=Closedness.CLOSED,
    )


def page(page_id="p1", width=100, height=100):
    return Page(id=page_id, width=width, height=height)


def codes(issues: list[Issue]) -> list[str]:
    return [issue.code for issue in issues]


# --- page bounds -----------------------------------------------------------


def test_page_bounds_reject_question_outside_page():
    issues = validate_page_bounds([page()], [question("1", make_box(x2=101))])
    assert codes(issues) == ["COORDINATE_OUT_OF_BOUNDS"]
    assert issues[0].refs == ["1"]
    assert issues[0].severity is Severity.BLOCKING


def test_page_bounds_use_each_page_size():
    pages = [page("p1", 100, 100), page("p2", 300, 300)]
    questions = [question("1", make_box(x2=250, y2=250, page_id="p2"))]
    assert validate_page_bounds(pages, questions) == []


def test_page_bounds_reject_unknown_page():
    issues = validate_page_bounds([page()], [question("1", make_box(page_id="p9"))])
    assert codes(issues) == ["PAGE_NOT_FOUND"]


def test_page_bounds_reject_duplicate_page_id():
    issues = validate_page_bounds([page(), page()], [])
    assert codes(issues) == ["DUPLICATE_PAGE_ID"]


def test_page_bounds_check_answer_boxes_and_skip_blank_answers():
    answers = [
        answer("a1", "1", bbox=make_box(y2=150)),
        answer("a2", "1", mode=AnswerMode.BLANK),
    ]
    issues = validate_page_bounds([page()], [question("1", make_box())], answers)
    assert codes(issues) == ["COORDINATE_OUT_OF_BOUNDS"]
    assert issues[0].refs == ["a1"]


# --- question hierarchy ----------------------------------------------------


def test_question_hierarchy_rejects_missing_parent():
    issues = validate_question_hierarchy([question("1-1", make_box(), parent_id="1")])
    assert codes(issues) == ["PARENT_NOT_FOUND"]


def test_question_hierarchy_rejects_child_outside_parent():
    questions = [question("1", make_box()), question("1-1", make_box(x1=90, x2=120), "1")]
    assert codes(validate_question_hierarchy(questions)) == ["CHILD_OUTSIDE_PARENT"]


def test_question_hierarchy_rejects_parent_on_other_page():
    questions = [
        question("1", make_box()),
        question("1-1", make_box(page_id="p2"), "1"),
    ]
    assert codes(validate_question_hierarchy(questions)) == ["PARENT_PAGE_MISMATCH"]


def test_question_hierarchy_rejects_self_parent():
    issues = validate_question_hierarchy([question("1", make_box(), parent_id="1")])
    assert codes(issues) == ["PARENT_CYCLE"]


def test_question_hierarchy_reports_each_cycle_once():
    questions = [
        question("1", make_box(), parent_id="2"),
        question("2", make_box(), parent_id="1"),
    ]
    issues = validate_question_hierarchy(questions)
    assert codes(issues) == ["PARENT_CYCLE"]
    assert issues[0].refs == ["1", "2"]


def test_question_hierarchy_rejects_duplicate_question_id():
    questions = [question("1", make_box()), question("1", make_box(x2=50))]
    assert codes(validate_question_hierarchy(questions)) == ["DUPLICATE_QUESTION_ID"]


def test_question_hierarchy_collects_all_issues_in_one_pass():
    questions = [
        question("1", make_box()),
        question("1", make_box(x2=50)),
        question("1-1", make_box(x1=90, x2=120), parent_id="1"),
        question("2-1", make_box(), parent_id="2"),
    ]
    assert sorted(codes(validate_question_hierarchy(questions))) == [
        "CHILD_OUTSIDE_PARENT",
        "DUPLICATE_QUESTION_ID",
        "PARENT_NOT_FOUND",
    ]


def test_question_hierarchy_accepts_valid_nested_tree():
    questions = [
        question("1", make_box()),
        question("1-1", make_box(x2=50), parent_id="1"),
        question("1-1-1", make_box(x2=20), parent_id="1-1"),
    ]
    assert validate_question_hierarchy(questions) == []


# --- answer bindings -------------------------------------------------------


def test_answer_binding_rejects_unknown_question():
    issues = validate_answer_bindings([], [answer("1-答1", "missing")])
    assert codes(issues) == ["QUESTION_NOT_FOUND"]
    assert issues[0].refs == ["1-答1", "missing"]


def test_answer_binding_collects_all_issues():
    answers = [answer("a1", "1"), answer("a1", "1"), answer("a2", "missing")]
    issues = validate_answer_bindings([question("1", make_box())], answers)
    assert sorted(codes(issues)) == ["DUPLICATE_ANSWER_ID", "QUESTION_NOT_FOUND"]


# --- full validation -------------------------------------------------------


def test_validate_annotation_passes_clean_input():
    result = validate_annotation(
        pages=[page()],
        questions=[question("1", make_box()), question("1-1", make_box(x2=50), "1")],
        answers=[answer("a1", "1-1", bbox=make_box(x2=40))],
        confidence=0.9,
    )
    assert result.status is ResultStatus.PASSED
    assert result.issues == []
    assert result.confidence == 0.9


def test_validate_annotation_collects_issues_from_every_validator():
    result = validate_annotation(
        pages=[page()],
        questions=[question("1", make_box(x2=150)), question("1", make_box())],
        answers=[answer("a1", "missing")],
    )
    assert result.status is ResultStatus.NEEDS_REVIEW
    assert sorted(codes(result.issues)) == [
        "COORDINATE_OUT_OF_BOUNDS",
        "DUPLICATE_QUESTION_ID",
        "QUESTION_NOT_FOUND",
    ]
