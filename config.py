from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-Powered Competency Learning Platform"
    app_env: str = "development"
    debug: bool = False

    mongodb_uri: str = "mongodb://localhost:27017/"
    database_name: str = "competency_learning_db"
    seed_on_start: bool = False

    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    secret_key: str = "change-this-development-secret"

    session_max_age_hours: int = Field(default=12, gt=0)
    max_ai_prompt_chars: int = Field(default=30000, gt=0)
    max_ai_output_chars: int = Field(default=20000, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env.strip().lower() == "production":
            if (
                len(self.secret_key) < 32
                or self.secret_key == "change-this-development-secret"
            ):
                raise ValueError(
                    "Production requires a strong SECRET_KEY of at least 32 characters."
                )

            if self.debug:
                raise ValueError("DEBUG must be disabled in production.")

        return self


def _load_streamlit_secrets():
    """Read flat Streamlit secrets when running in Streamlit Cloud."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        try:
            values = dict(st.secrets)
        except StreamlitSecretNotFoundError:
            return {}

    except ImportError:
        return {}

    allowed_fields = set(Settings.model_fields)

    return {
        key.lower(): value
        for key, value in values.items()
        if key.lower() in allowed_fields and not isinstance(value, dict)
    }


@lru_cache
def get_settings():
    """Load Streamlit secrets with environment and .env fallbacks."""
    return Settings(**_load_streamlit_secrets())


settings = get_settings()
