from database.repositories.learning_repository import LearningRepository


class ProgressService:
    def __init__(self, db):
        self.repo = LearningRepository(db)

    def notify(self, user_id, message, kind="info"):
        self.repo.notify(user_id, message, kind)

    def notifications(self, user_id):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        return list(
            self.repo.notifications.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(30)
        )

    def log_ai(self, user_id, agent, prompt, output, status):
        self.repo.log_ai(user_id, agent, prompt, output, status)
