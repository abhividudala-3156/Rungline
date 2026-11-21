from agents.assessment_agent import AssessmentGenerationAgent
from agents.competency_agent import CompetencyAnalysisAgent
from agents.feedback_agent import EvaluationFeedbackAgent
from agents.learning_path_agent import LearningPathAgent
from agents.progress_agent import ProgressMonitoringAgent
from services.progress_service import ProgressService


class LearningOrchestrator:
    """Coordinates specialist agents; persistence remains in services/repositories."""

    def __init__(self, db=None, llm_client=None):
        self.competency = CompetencyAnalysisAgent()
        self.learning = LearningPathAgent(llm_client)
        self.assessment = AssessmentGenerationAgent(llm_client)
        self.feedback = EvaluationFeedbackAgent()
        self.progress = ProgressMonitoringAgent()
        self.progress_service = ProgressService(db) if db is not None else None

    def analyze(self, gap_report):
        return self.competency.run(gap_report)

    def generate_learning_path(
        self, user_id, career_code, career_title, gap_report, resources
    ):
        path = self.learning.run(career_code, career_title, gap_report, resources)
        if self.progress_service:
            self.progress_service.log_ai(
                user_id,
                self.learning.name,
                "gap report and approved resources",
                "Learning path generated successfully.",
                "success",
            )
        return path

    def generate_question(self, competency_name, difficulty="beginner"):
        return self.assessment.run(competency_name, difficulty)

    def feedback_for(self, career_title, gap_report):
        return self.feedback.run(career_title, gap_report)

    def monitor_progress(self, attempts, progress_records):
        return self.progress.run(attempts, progress_records)
