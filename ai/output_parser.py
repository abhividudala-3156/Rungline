import json

from models.ai_response import GeneratedQuestion, RecommendationResponse


def _extract_json(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI response did not contain a JSON object.")
    return json.loads(text[start : end + 1])


def parse_recommendation(raw):
    return RecommendationResponse.model_validate(_extract_json(raw)).model_dump()


def parse_question(raw):
    return GeneratedQuestion.model_validate(_extract_json(raw)).model_dump()
