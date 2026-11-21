from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


class LearningRepository:
    def __init__(self, db):
        self.paths = db.learning_paths
        self.progress = db.learning_progress
        self.notifications = db.notifications
        self.ai_logs = db.ai_interactions

    def save_path(self, user_id, career_code, path):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(career_code, str) or not career_code.strip():
            raise ValueError("A valid career code is required.")

        if not isinstance(path, dict):
            raise ValueError("Learning path must be a dictionary.")

        if path.get("career_code") != career_code.strip():
            raise ValueError("Learning path career code does not match.")

        doc = {
            "user_id": user_id,
            "career_code": career_code.strip(),
            "path": path,
            "created_at": datetime.now(timezone.utc),
            "status": "active",
        }

        return self.paths.insert_one(doc).inserted_id

    def latest_path(self, user_id):
        return self.paths.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )

    def set_progress(self, user_id, resource_id, completed):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(resource_id, str):
            raise ValueError("A valid learning resource ID is required.")

        if not isinstance(completed, bool):
            raise ValueError("Progress completion must be a Boolean value.")

        try:
            path_id, step_number = resource_id.rsplit(":", 1)
            path_object_id = ObjectId(path_id)
            step_number = int(step_number)

        except (ValueError, TypeError, InvalidId):
            raise ValueError("Invalid learning resource ID.") from None

        if step_number < 1:
            raise ValueError("Invalid learning step number.")

        path = self.paths.find_one(
            {
                "_id": path_object_id,
                "user_id": user_id,
            }
        )

        if not path:
            raise ValueError("Learning roadmap not found for this user.")

        path_data = path.get("path")

        if not isinstance(path_data, dict):
            raise ValueError("The saved learning roadmap is invalid.")

        steps = path_data.get("steps", [])

        if not isinstance(steps, list) or step_number > len(steps):
            raise ValueError("Learning step does not exist.")

        now = datetime.now(timezone.utc)

        self.progress.update_one(
            {
                "user_id": user_id,
                "resource_id": resource_id,
            },
            {
                "$set": {
                    "completed": completed,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

    def progress_for_user(self, user_id):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        return list(self.progress.find({"user_id": user_id}))

    def notify(self, user_id, message, kind="info"):
        allowed_kinds = {"info", "success", "warning", "error"}

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Notification message cannot be empty.")

        if len(message) > 500:
            raise ValueError("Notification message is too long.")

        if not isinstance(kind, str) or kind not in allowed_kinds:
            raise ValueError("Invalid notification type.")

        self.notifications.insert_one(
            {
                "user_id": user_id,
                "message": message.strip(),
                "kind": kind,
                "read": False,
                "created_at": datetime.now(timezone.utc),
            }
        )

    def log_ai(self, user_id, agent, prompt_summary, output_summary, status):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid user ID is required.")

        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("AI agent name cannot be empty.")

        if not isinstance(prompt_summary, str):
            raise ValueError("AI prompt summary must be text.")

        if not isinstance(output_summary, str):
            raise ValueError("AI output summary must be text.")

        if not isinstance(status, str) or not status.strip():
            raise ValueError("AI log status cannot be empty.")

        self.ai_logs.insert_one(
            {
                "user_id": user_id,
                "agent": agent.strip()[:100],
                "prompt_summary": prompt_summary[:500],
                "output_summary": output_summary[:1000],
                "status": status.strip()[:30],
                "created_at": datetime.now(timezone.utc),
            }
        )
