from pydantic import BaseModel, ConfigDict, Field, field_validator


class LearningStep(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    competency_code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=150)
    objective: str = Field(min_length=1, max_length=1000)

    activities: list[str] = Field(
        default_factory=list,
        max_length=15,
    )

    resource_urls: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    estimated_hours: float = Field(ge=0, le=500, default=2)
    priority: int = Field(ge=1, le=10, default=5)

    @field_validator("activities")
    @classmethod
    def validate_activities(cls, values):
        if any(not value or len(value) > 500 for value in values):
            raise ValueError("Each activity must contain 1 to 500 characters.")
        return values

    @field_validator("resource_urls")
    @classmethod
    def validate_resource_urls(cls, values):
        if any(not value or len(value) > 2048 for value in values):
            raise ValueError("Each resource URL must contain 1 to 2048 characters.")
        return values


class LearningPath(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    career_code: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=10, max_length=1500)
    steps: list[LearningStep] = Field(
        min_length=1,
        max_length=30,
    )
