
from datetime import datetime, timezone


class AssessmentRepository:
    MAX_HISTORY_LIMIT = 200

    def __init__(self, db):
        self.questions, self.attempts = db.questions, db.assessment_attempts

    def questions_for_career(self, career_code, competency_codes=None):
        query = {"career_code": career_code, "is_active": True}

        if competency_codes:
            query["competency_code"] = {"$in": list(competency_codes)}

        return list(self.questions.find(query))

    def save_attempt(self, user_id, career_code, result):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(career_code, str) or not career_code.strip():
            raise ValueError("A valid career code is required.")

        if not isinstance(result, dict):
            raise ValueError("Assessment result must be a dictionary.")

        allowed_fields = {
            "answers",
            "skill_scores",
            "total_attempted",
            "total_questions",
            "overall_score",
        }

        safe_result = {
            key: value
            for key, value in result.items()
            if key in allowed_fields
        }

        doc = {
            **safe_result,
            "user_id": user_id,
            "career_code": career_code.strip(),
            "created_at": datetime.now(timezone.utc),
        }

        return self.attempts.insert_one(doc).inserted_id

    def history(self, user_id, limit=20):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("Assessment history limit must be an integer.")

        limit = max(1, min(limit, self.MAX_HISTORY_LIMIT))

        return list(
            self.attempts.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
