from services.recommendation_service import RecommendationService


class EvaluationFeedbackAgent:
    name = "evaluation_feedback"

    def __init__(self, service=None):
        self.service = service or RecommendationService()

    def run(self, career_title, gap_report):
        return self.service.recommend(career_title, gap_report)
