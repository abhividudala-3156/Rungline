from database.repositories.assessment_repository import AssessmentRepository
from services.competency_service import CompetencyService


class AssessmentService:
    def __init__(self, db):
        self.repo = AssessmentRepository(db)
        self.competency = CompetencyService()

    def questions(self, career_code):
        return self.repo.questions_for_career(career_code)

    def submit(self, user_id, career_code, answers):
        questions = self.questions(career_code)
        if not questions:
            raise ValueError("No questions are available for this career yet.")
        valid_codes = {q["code"] for q in questions}
        if not set(answers).issubset(valid_codes):
            raise ValueError("Submission contains an unknown question.")
        scores = self.competency.aggregate_answers(questions, answers)
        total_attempted = sum(1 for q in questions if q["code"] in answers)
        total_correct = sum(
            1
            for q in questions
            if q["code"] in answers and answers[q["code"]] == q["correct_option"]
        )
        result = {
            "answers": [
                {"question_code": k, "selected_option": v} for k, v in answers.items()
            ],
            "skill_scores": scores,
            "total_attempted": total_attempted,
            "total_questions": len(questions),
            "overall_score": round(total_correct / total_attempted * 100, 2)
            if total_attempted
            else None,
        }
        attempt_id = self.repo.save_attempt(user_id, career_code, result)
        return {"attempt_id": str(attempt_id), **result}

    def history(self, user_id):
        return self.repo.history(user_id)
