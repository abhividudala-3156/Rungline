
import secrets

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def generate_secret_key() -> str:
    return secrets.token_urlsafe(48)


def password_policy(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if len(password.encode("utf-8")) > 72:
        return False, "Password must not exceed 72 UTF-8 bytes."

    if not any(c.isalpha() for c in password) or not any(
        c.isdigit() for c in password
    ):
        return False, "Password must contain at least one letter and one number."

    return True, ""
