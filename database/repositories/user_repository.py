from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


class UserRepository:
    MAX_USER_LIMIT = 200

    def __init__(self, db):
        self.col = db.users

    def create(self, data):
        now = datetime.now(timezone.utc)

        doc = {
            **data,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }

        return self.col.insert_one(doc).inserted_id

    def by_email(self, email):
        return self.col.find_one({"email": email.lower().strip()})

    def by_id(self, user_id):
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            return None

        return self.col.find_one({"_id": object_id})

    def update_career_goal(self, user_id, career_code):
        if not isinstance(career_code, str) or not career_code.strip():
            raise ValueError("A valid career code is required.")

        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            raise ValueError("A valid user ID is required.") from None

        result = self.col.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "career_code": career_code.strip(),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        return result.matched_count == 1

    def list_users(self, limit=200):
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("User limit must be an integer.")

        limit = max(1, min(limit, self.MAX_USER_LIMIT))

        return list(
            self.col.find(
                {},
                {"password_hash": 0},
            )
            .sort("created_at", -1)
            .limit(limit)
        )
