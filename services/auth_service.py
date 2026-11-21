from pymongo.errors import DuplicateKeyError

from database.repositories.user_repository import UserRepository
from utils.security import hash_password, password_policy, verify_password
from utils.validators import validate_registration


class AuthService:
    def __init__(self, db):
        self.db = db
        self.users = UserRepository(db)

    def register(self, name, email, password):
        ok, message = validate_registration(name, email, password)
        if not ok:
            raise ValueError(message)

        ok, message = password_policy(password)
        if not ok:
            raise ValueError(message)

        email = email.strip().lower()

        if self.users.by_email(email):
            raise ValueError("An account with this email already exists.")

        try:
            user_id = self.users.create(
                {
                    "name": name.strip(),
                    "email": email,
                    "password_hash": hash_password(password),
                    "role": "learner",
                }
            )
        except DuplicateKeyError:
            raise ValueError("An account with this email already exists.") from None

        return str(user_id)

    def login(self, email, password):
        user = self.users.by_email(email.strip().lower())

        if (
            not user
            or not user.get("is_active")
            or not verify_password(password, user.get("password_hash", ""))
        ):
            return None

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        }

    def bootstrap_initial_admin(self, email, password):
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValueError("Valid administrator credentials are required.")

        email = email.strip().lower()

        if not email or not password:
            raise ValueError("Administrator email and password are required.")

        ok, message = validate_registration(
            "Administrator",
            email,
            password,
        )
        if not ok:
            raise ValueError(message)

        ok, message = password_policy(password)
        if not ok:
            raise ValueError(message)

        if self.db.users.count_documents({"role": "admin"}) > 0:
            raise ValueError(
                "An administrator account already exists. "
                "Initial administrator setup is disabled."
            )

        if self.users.by_email(email):
            raise ValueError("An account with this email already exists.")

        try:
            user_id = self.users.create(
                {
                    "name": "Administrator",
                    "email": email,
                    "password_hash": hash_password(password),
                    "role": "admin",
                }
            )
        except DuplicateKeyError as exc:
            if "one_administrator_only" in str(exc):
                raise ValueError(
                    "An administrator account already exists. "
                    "Initial administrator setup is disabled."
                ) from None

            raise ValueError("An account with this email already exists.") from None

        return str(user_id)
