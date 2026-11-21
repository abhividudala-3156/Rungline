from database.repositories.learning_repository import LearningRepository
from models.learning_path import LearningPath


class LearningService:
    def __init__(self, db):
        self.repo = LearningRepository(db)

    def save_path(self, user_id, career_code, path):
        validated = LearningPath.model_validate(path)
        return str(self.repo.save_path(user_id, career_code, validated.model_dump()))

    def latest_path(self, user_id):
        return self.repo.latest_path(user_id)

    def set_progress(self, user_id, resource_id, completed):
        self.repo.set_progress(user_id, resource_id, completed)

    def progress(self, user_id):
        return self.repo.progress_for_user(user_id)
