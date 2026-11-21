
import pytest
from pydantic import ValidationError

from config import Settings


def test_development_settings_accept_default_secret():
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.secret_key == "change-this-development-secret"


def test_production_requires_strong_secret():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            secret_key="weak-secret",
        )


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            secret_key="change-this-development-secret",
        )


def test_production_rejects_debug_mode():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            secret_key="a" * 40,
            debug=True,
        )


def test_production_accepts_valid_settings():
    settings = Settings(
        _env_file=None,
        app_env="production",
        secret_key="a" * 40,
        debug=False,
    )

    assert settings.app_env == "production"
    assert settings.debug is False


def test_session_duration_must_be_positive():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, session_max_age_hours=0)


def test_ai_output_limit_must_be_positive():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, max_ai_output_chars=0)
