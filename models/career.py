from pydantic import BaseModel, Field


class Career(BaseModel):
    code: str
    title: str
    description: str = ""
    is_active: bool = True


class CareerRequirement(BaseModel):
    career_code: str
    competency_code: str
    required_level: int = Field(ge=1, le=5)
    weight: float = Field(gt=0, le=1)
