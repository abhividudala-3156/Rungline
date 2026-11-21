import pytest
from pydantic import ValidationError

import config
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


def test_get_settings_uses_streamlit_secrets(monkeypatch):
    monkeypatch.setattr(
        config,
        "_load_streamlit_secrets",
        lambda: {
            "app_env": "production",
            "secret_key": "s" * 40,
            "debug": False,
            "database_name": "rungline_production",
        },
    )

    config.get_settings.cache_clear()

    try:
        settings = config.get_settings()

        assert settings.app_env == "production"
        assert settings.database_name == "rungline_production"
        assert settings.debug is False
    finally:
        config.get_settings.cache_clear()


def test_streamlit_secret_keys_are_filtered(monkeypatch):
    monkeypatch.setattr(
        config,
        "_load_streamlit_secrets",
        lambda: {
            "database_name": "rungline_test",
            "unknown_setting": "ignored",
        },
    )

    config.get_settings.cache_clear()

    try:
        settings = config.get_settings()

        assert settings.database_name == "rungline_test"
        assert not hasattr(settings, "unknown_setting")
    finally:
        config.get_settings.cache_clear()
