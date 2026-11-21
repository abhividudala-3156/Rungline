import pytest

from services.auth_service import AuthService
from tests.conftest import FakeDB
from utils.security import password_policy


def test_registration_and_login():
    service = AuthService(FakeDB())

    uid = service.register(
        "Sample Learner",
        "sample@example.com",
        "StrongPass123",
    )

    assert uid

    result = service.login("SAMPLE@example.com", "StrongPass123")

    assert result["email"] == "sample@example.com"
    assert result["role"] == "learner"

    assert service.login("sample@example.com", "wrongpass") is None


def test_initial_admin_creation():
    db = FakeDB()
    service = AuthService(db)

    uid = service.bootstrap_initial_admin(
        "admin@example.com",
        "AdminPass123",
    )

    assert uid
    assert db.users.count_documents({"role": "admin"}) == 1

    admin = service.login("admin@example.com", "AdminPass123")

    assert admin["role"] == "admin"


def test_second_admin_creation_is_rejected():
    db = FakeDB()
    service = AuthService(db)

    service.bootstrap_initial_admin(
        "admin@example.com",
        "AdminPass123",
    )

    with pytest.raises(ValueError, match="administrator account already exists"):
        service.bootstrap_initial_admin(
            "another@example.com",
            "AnotherPass123",
        )

    assert db.users.count_documents({"role": "admin"}) == 1


def test_initial_admin_requires_credentials():
    service = AuthService(FakeDB())

    with pytest.raises(ValueError, match="email and password are required"):
        service.bootstrap_initial_admin("", "")


def test_initial_admin_rejects_invalid_email():
    service = AuthService(FakeDB())

    with pytest.raises(ValueError):
        service.bootstrap_initial_admin(
            "invalid-email",
            "AdminPass123",
        )


def test_initial_admin_rejects_invalid_password():
    service = AuthService(FakeDB())

    with pytest.raises(ValueError, match="8 characters"):
        service.bootstrap_initial_admin(
            "admin@example.com",
            "Ab123",
        )


def test_initial_admin_rejects_existing_email():
    db = FakeDB()
    service = AuthService(db)

    service.register(
        "Existing Learner",
        "admin@example.com",
        "LearnerPass123",
    )

    with pytest.raises(ValueError, match="email already exists"):
        service.bootstrap_initial_admin(
            "admin@example.com",
            "AdminPass123",
        )


def test_password_minimum_length():
    ok, message = password_policy("Ab123")

    assert not ok
    assert "8 characters" in message


def test_password_utf8_byte_limit():
    password = "A" * 70 + "12"

    ok, message = password_policy(password)

    assert ok
    assert message == ""

    long_password = "A" * 71 + "12"

    ok, message = password_policy(long_password)

    assert not ok
    assert "72 UTF-8 bytes" in message


def test_password_requires_letter_and_number():
    assert password_policy("PasswordOnly")[0] is False
    assert password_policy("12345678")[0] is False
    assert password_policy("Password123")[0] is True
