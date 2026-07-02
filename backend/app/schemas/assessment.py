from typing import Optional

from pydantic import BaseModel


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: str  # A, B, C, D, T, or F


class AssessmentSubmit(BaseModel):
    video_id: int
    answers: list[AnswerSubmit]
