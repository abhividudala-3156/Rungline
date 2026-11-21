from pydantic import BaseModel, Field


class Competency(BaseModel):
    code: str
    name: str
    category: str
    description: str = ""


class CompetencyEvidence(BaseModel):
    competency_code: str
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1, default=1.0)
