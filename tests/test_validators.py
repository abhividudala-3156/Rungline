
import pytest

from utils.validators import validate_registration


@pytest.mark.parametrize(
    ("name", "email", "password"),
    [
        (None, "user@example.com", "StrongPass123"),
        ("Sample User", None, "StrongPass123"),
        ("Sample User", "user@example.com", None),
        (123, "user@example.com", "StrongPass123"),
        ("Sample User", ["user@example.com"], "StrongPass123"),
    ],
)
def test_registration_rejects_non_string_inputs(name, email, password):
    valid, message = validate_registration(name, email, password)

    assert valid is False
    assert message == "All registration fields must contain text."


def test_registration_accepts_valid_input():
    valid, message = validate_registration(
        "Sample Learner",
        "sample@example.com",
        "StrongPass123",
    )

    assert valid is True
    assert message == ""


@pytest.mark.parametrize(
    ("name", "email", "password"),
    [
        ("A", "sample@example.com", "StrongPass123"),
        ("Sample Learner", "invalid-email", "StrongPass123"),
        ("Sample Learner", "sample@example.com", "short"),
    ],
)
def test_registration_rejects_invalid_values(name, email, password):
    valid, message = validate_registration(name, email, password)

    assert valid is False
    assert message
