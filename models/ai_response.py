from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    summary: str = Field(min_length=10, max_length=1000)
    recommendations: list[str] = Field(min_length=1, max_length=12)

    @field_validator("recommendations")
    @classmethod
    def validate_recommendations(cls, values):
        for value in values:
            if not value or len(value) > 500:
                raise ValueError(
                    "Each recommendation must contain 1 to 500 characters."
                )
        return values


class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    prompt: str = Field(min_length=8, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_option: int = Field(strict=True, ge=0)
    explanation: str = Field(min_length=10, max_length=1000)

    @field_validator("options")
    @classmethod
    def validate_options(cls, values):
        if any(not option or len(option) > 300 for option in values):
            raise ValueError("Each option must contain 1 to 300 characters.")

        normalized = [option.casefold() for option in values]

        if len(normalized) != len(set(normalized)):
            raise ValueError("Answer options must be unique.")

        return values

    @model_validator(mode="after")
    def validate_correct_option(self):
        if self.correct_option >= len(self.options):
            raise ValueError("correct_option must refer to an existing option index.")

        return self
