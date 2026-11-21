import sys
import types
from types import SimpleNamespace

import pytest

from ai.llm_client import LLMClient
from config import settings


def install_fake_genai(monkeypatch, client_factory):
    google_module = types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")

    genai_module.Client = client_factory
    google_module.genai = genai_module

    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)


def configure_gemini(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-api-key")
    monkeypatch.setattr(settings, "gemini_model", "test-model")


def test_reject_unsupported_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "unsupported")

    client = LLMClient(api_key="test-key")

    with pytest.raises(RuntimeError, match="unsupported"):
        client.generate("Test prompt")


def test_reject_missing_api_key(monkeypatch):
    configure_gemini(monkeypatch)

    client = LLMClient(api_key="")

    with pytest.raises(RuntimeError, match="API key is missing"):
        client.generate("Test prompt")


@pytest.mark.parametrize("prompt", ["", "   ", None, 123])
def test_reject_invalid_prompt(monkeypatch, prompt):
    configure_gemini(monkeypatch)

    client = LLMClient(api_key="test-key")

    with pytest.raises(ValueError, match="valid AI prompt"):
        client.generate(prompt)


def test_successful_generation(monkeypatch):
    configure_gemini(monkeypatch)

    def client_factory(api_key):
        assert api_key == "test-key"

        return SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(
                    text="Generated response"
                )
            )
        )

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key", model="test-model")

    result = client.generate("Test prompt")

    assert result == "Generated response"


def test_non_retryable_error_is_sanitized(monkeypatch):
    configure_gemini(monkeypatch)

    def generate_content(**kwargs):
        raise RuntimeError("Sensitive provider error and secret information")

    def client_factory(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content)
        )

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key")

    with pytest.raises(RuntimeError) as error:
        client.generate("Test prompt")

    assert "Sensitive provider error" not in str(error.value)
    assert "secret information" not in str(error.value)


def test_retryable_error_exhausts_attempts(monkeypatch):
    configure_gemini(monkeypatch)

    calls = []

    class TemporaryError(Exception):
        code = 503

    def generate_content(**kwargs):
        calls.append(kwargs)
        raise TemporaryError("Temporary provider failure")

    def client_factory(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content)
        )

    install_fake_genai(monkeypatch, client_factory)
    monkeypatch.setattr("ai.llm_client.time.sleep", lambda seconds: None)

    client = LLMClient(api_key="test-key")

    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        client.generate("Test prompt")

    assert len(calls) == 3


def test_retry_succeeds_on_second_attempt(monkeypatch):
    configure_gemini(monkeypatch)

    calls = []
    delays = []

    class TemporaryError(Exception):
        code = 503

    def generate_content(**kwargs):
        calls.append(kwargs)

        if len(calls) == 1:
            raise TemporaryError("Temporary failure")

        return SimpleNamespace(text="Success after retry")

    def client_factory(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content)
        )

    install_fake_genai(monkeypatch, client_factory)
    monkeypatch.setattr(
        "ai.llm_client.time.sleep",
        lambda seconds: delays.append(seconds),
    )

    client = LLMClient(api_key="test-key")

    result = client.generate("Test prompt")

    assert result == "Success after retry"
    assert len(calls) == 2
    assert delays == [2]


def test_empty_response_is_rejected(monkeypatch):
    configure_gemini(monkeypatch)

    def client_factory(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(text=" ")
            )
        )

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key")

    with pytest.raises(RuntimeError, match="empty response"):
        client.generate("Test prompt")


def test_client_initialization_error_is_sanitized(monkeypatch):
    configure_gemini(monkeypatch)

    def client_factory(api_key):
        raise RuntimeError("Sensitive initialization details")

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key")

    with pytest.raises(RuntimeError) as error:
        client.generate("Test prompt")

    assert "Sensitive initialization details" not in str(error.value)


def test_oversized_prompt_is_rejected_before_client_initialization(
    monkeypatch,
):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(settings, "max_ai_prompt_chars", 10)

    def client_factory(api_key):
        pytest.fail("Gemini client should not be initialized.")

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key")

    with pytest.raises(ValueError, match="size limit"):
        client.generate("A" * 11)


def test_prompt_at_configured_limit_is_accepted(monkeypatch):
    configure_gemini(monkeypatch)
    monkeypatch.setattr(settings, "max_ai_prompt_chars", 10)

    def client_factory(api_key):
        return SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(
                    text="Generated response"
                )
            )
        )

    install_fake_genai(monkeypatch, client_factory)

    client = LLMClient(api_key="test-key")

    result = client.generate("A" * 10)

    assert result == "Generated response"
