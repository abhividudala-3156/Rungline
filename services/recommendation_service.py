from ai.guardrails import validate_text_output
from ai.llm_client import LLMClient
from ai.output_parser import parse_recommendation
from ai.prompt_templates import recommendation_prompt


class RecommendationService:
    def __init__(self, client=None):
        self.client = client or LLMClient()

    def recommend(self, career_title, gap_report):
        prompt = recommendation_prompt(career_title, gap_report)
        raw = self.client.generate(prompt)
        validate_text_output(raw)
        return parse_recommendation(raw)
