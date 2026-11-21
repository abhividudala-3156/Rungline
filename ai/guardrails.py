from config import settings


def validate_text_output(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("AI output is empty.")
    if len(text) > settings.max_ai_output_chars:
        raise ValueError("AI output exceeds the configured size limit.")
    return text


def validate_resource_urls(urls, approved_urls):
    approved = set(approved_urls)
    return [url for url in urls if url in approved]
