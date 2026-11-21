from pydantic import ValidationError

from models.user import UserCreate


def validate_registration(name, email, password):
    if not all(isinstance(value, str) for value in (name, email, password)):
        return False, "All registration fields must contain text."

    try:
        UserCreate(
            name=name.strip(),
            email=email.strip().lower(),
            password=password,
        )
        return True, ""
    except ValidationError as exc:
        return False, "; ".join(error["msg"] for error in exc.errors())
