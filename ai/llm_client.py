import logging
import time

from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Gemini API client with safe error handling and retry support."""

    MAX_ATTEMPTS = 3
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model

    def generate(self, prompt: str) -> str:
        if settings.ai_provider.lower() != "gemini":
            raise RuntimeError("The configured AI provider is unsupported.")

        if not self.api_key:
            raise RuntimeError("Gemini API key is missing. Add GEMINI_API_KEY to .env.")

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A valid AI prompt is required.")

        if len(prompt) > settings.max_ai_prompt_chars:
            raise ValueError("AI prompt exceeds the configured size limit.")

        from google import genai

        try:
            client = genai.Client(api_key=self.api_key)
        except Exception:
            logger.error("Gemini client initialization failed.")
            raise RuntimeError(
                "Unable to initialize the Gemini client. Check the AI configuration."
            ) from None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
            except Exception as exc:
                status_code = getattr(
                    exc,
                    "code",
                    getattr(exc, "status_code", None),
                )

                if status_code not in self.RETRYABLE_STATUS_CODES:
                    logger.error("Gemini request failed with a non-retryable error.")
                    raise RuntimeError(
                        "The Gemini request could not be completed. "
                        "Please check the AI configuration and try again."
                    ) from None

                if attempt == self.MAX_ATTEMPTS:
                    logger.error(
                        "Gemini request failed after %s attempts.",
                        self.MAX_ATTEMPTS,
                    )
                    raise RuntimeError(
                        "Gemini is temporarily unavailable. Please try again later."
                    ) from None

                wait_seconds = 2**attempt

                logger.warning(
                    "Gemini returned HTTP %s. Retrying in %s seconds "
                    "(attempt %s of %s).",
                    status_code,
                    wait_seconds,
                    attempt,
                    self.MAX_ATTEMPTS,
                )

                time.sleep(wait_seconds)
                continue

            text = getattr(response, "text", None)

            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("The AI provider returned an empty response.")

            return text

        raise RuntimeError("Gemini request could not be completed.")
