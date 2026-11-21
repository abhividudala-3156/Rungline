from datetime import datetime, timezone


class AuditLogRepository:
    MAX_LOG_LIMIT = 200

    ALLOWED_ACTIONS = {
        "database.indexes.ensure",
        "database.seed.update",
        "auth.initial_admin.bootstrap",
    }

    ALLOWED_OUTCOMES = {"success", "failure"}

    ALLOWED_TARGET_TYPES = {"platform", "database"}

    ALLOWED_DETAIL_KEYS = {"collection", "count", "operation"}

    def __init__(self, db):
        self.col = db.audit_logs

    def record(
        self,
        actor,
        action,
        outcome,
        target_type="platform",
        target_id=None,
        details=None,
    ):
        if not isinstance(actor, dict):
            raise ValueError("A valid actor is required.")

        actor_id = actor.get("id")
        actor_email = actor.get("email")
        actor_role = actor.get("role")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (actor_id, actor_email, actor_role)
        ):
            raise ValueError("Actor identity is incomplete.")

        if actor_role != "admin":
            raise ValueError("Only administrators can record these actions.")

        if action not in self.ALLOWED_ACTIONS:
            raise ValueError("Unsupported audit action.")

        if outcome not in self.ALLOWED_OUTCOMES:
            raise ValueError("Invalid audit outcome.")

        if target_type not in self.ALLOWED_TARGET_TYPES:
            raise ValueError("Invalid audit target type.")

        if target_id is not None and (
            not isinstance(target_id, str) or len(target_id) > 100
        ):
            raise ValueError("Invalid audit target ID.")

        if details is None:
            details = {}

        if not isinstance(details, dict):
            raise ValueError("Audit details must be a dictionary.")

        if not set(details).issubset(self.ALLOWED_DETAIL_KEYS):
            raise ValueError("Audit details contain unsupported fields.")

        safe_details = {}

        for key, value in details.items():
            if key == "count":
                if not isinstance(value, int) or isinstance(value, bool):
                    raise ValueError("Audit count must be an integer.")
                if value < 0:
                    raise ValueError("Audit count cannot be negative.")
            elif key in {"collection", "operation"}:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"Invalid audit detail: {key}.")
                if len(value) > 100:
                    raise ValueError(f"Audit detail is too long: {key}.")

            safe_details[key] = value

        document = {
            "actor_id": actor_id.strip(),
            "actor_email": actor_email.strip().lower(),
            "actor_role": actor_role,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "outcome": outcome,
            "details": safe_details,
            "created_at": datetime.now(timezone.utc),
        }

        return self.col.insert_one(document).inserted_id

    def list_recent(self, actor, limit=100):
        if not isinstance(actor, dict) or actor.get("role") != "admin":
            raise ValueError("Only administrators can view audit logs.")

        if not all(
            isinstance(actor.get(key), str) and actor[key].strip()
            for key in ("id", "email")
        ):
            raise ValueError("Administrator identity is incomplete.")

        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("Audit log limit must be an integer.")

        limit = max(1, min(limit, self.MAX_LOG_LIMIT))

        return list(self.col.find({}).sort("created_at", -1).limit(limit))
