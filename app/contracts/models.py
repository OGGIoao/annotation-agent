from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Subject(StrEnum):
    MATH = "数学"


class QuestionType(StrEnum):
    CHOICE = "选择题"
    FILL_IN = "填空题"
    TRUE_FALSE = "判断题"
    MENTAL_ARITHMETIC = "口算题"
    CALCULATION = "计算题"
    WORD_PROBLEM = "解答题"
    MATCHING = "连线题"
    READING = "阅读理解"


class LineType(StrEnum):
    SOLID = "实线"
    EXAMPLE = "例题"
    REMNANT = "残题"
    NO_ANSWER = "无答案/略"


class AnswerMode(StrEnum):
    TEXT = "text"
    FORMULA = "formula"
    IMAGE = "image"
    BLANK = "blank"


class Closedness(StrEnum):
    CLOSED = "封闭"
    SEMANTICALLY_EQUIVALENT = "语义一致即可"
    FINITE = "有限答案"
    CONDITIONALLY_OPEN = "有条件开放（符合常理即可）"
    INTERDEPENDENT = "有条件开放（答案框相互制约）"
    FULLY_OPEN = "完全开放"


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    page_id: str = Field(min_length=1)
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(ge=0)
    y2: float = Field(ge=0)

    @model_validator(mode="after")
    def has_positive_area(self) -> "BoundingBox":
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("bounding box must have positive width and height")
        return self


class QuestionNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    bbox: BoundingBox
    subject: Subject
    types: list[QuestionType] = Field(min_length=1)
    line_type: LineType
    parent_id: str | None = None
    is_example: bool = False
    is_duplicate: bool = False
    is_similar: bool = False


class AnswerBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    bbox: BoundingBox | None = None
    text: str | None = None
    mode: AnswerMode
    closedness: Closedness

    @model_validator(mode="after")
    def require_content_for_non_blank(self) -> "AnswerBox":
        if self.mode is not AnswerMode.BLANK and self.bbox is None:
            raise ValueError("non-blank answer boxes require a bounding box")
        return self
