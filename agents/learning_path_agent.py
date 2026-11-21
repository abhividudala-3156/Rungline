from ai.guardrails import validate_resource_urls, validate_text_output
from ai.llm_client import LLMClient
from ai.output_parser import _extract_json
from ai.prompt_templates import learning_path_prompt
from models.learning_path import LearningPath


class LearningPathAgent:
    name = "learning_path"

    def __init__(self, client=None):
        self.client = client or LLMClient()

    def run(self, career_code, career_title, gap_report, resources):
        prompt = learning_path_prompt(career_title, gap_report, resources)
        raw = validate_text_output(self.client.generate(prompt))
        data = _extract_json(raw)
        data["career_code"] = career_code
        approved = [r["url"] for r in resources if r.get("url")]
        for step in data.get("steps", []):
            step["resource_urls"] = validate_resource_urls(
                step.get("resource_urls", []), approved
            )
        return LearningPath.model_validate(data).model_dump()
