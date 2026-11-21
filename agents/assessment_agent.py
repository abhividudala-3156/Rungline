from ai.guardrails import validate_text_output
from ai.llm_client import LLMClient
from ai.output_parser import parse_question
from ai.prompt_templates import assessment_prompt


class AssessmentGenerationAgent:
    name = "assessment_generation"

    def __init__(self, client=None):
        self.client = client or LLMClient()

    def run(self, competency_name, difficulty="beginner"):
        raw = validate_text_output(
            self.client.generate(assessment_prompt(competency_name, difficulty))
        )
        return parse_question(raw)
