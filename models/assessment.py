from pydantic import BaseModel, Field


class Question(BaseModel):
    code: str
    career_code: str
    competency_code: str
    prompt: str
    options: list[str] = Field(min_length=2)
    correct_option: int = Field(ge=0)
    explanation: str = ""
    difficulty: str = "beginner"


class AssessmentAnswer(BaseModel):
    question_code: str
    selected_option: int = Field(ge=0)
