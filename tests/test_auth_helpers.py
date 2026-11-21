from datetime import datetime, timedelta, timezone

import pytest

import utils.auth as auth


class StopExecutionError(Exception):
    """Represents Streamlit's stop behavior in tests."""


class FakeSessionState(dict):
    """Minimal dictionary supporting Streamlit-style attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class FakeUserRepository:
    def __init__(self, db):
        self.db = db

    def by_id(self, user_id):
        return {
            "_id": user_id,
            "name": "Sample Learner",
            "email": "sample@example.com",
            "role": "learner",
            "is_active": True,
        }


def prepare_session(monkeypatch, session):
    monkeypatch.setattr(auth.st, "session_state", session)

    def stop():
        raise StopExecutionError

    monkeypatch.setattr(auth.st, "stop", stop)
    monkeypatch.setattr(auth.st, "info", lambda message: None)
    monkeypatch.setattr(auth.st, "warning", lambda message: None)


def test_valid_session_is_accepted(monkeypatch):
    session = FakeSessionState(
        {
            "user": {
                "id": "user-1",
                "name": "Sample Learner",
            },
            "authenticated_at": datetime.now(timezone.utc),
        }
    )

    prepare_session(monkeypatch, session)

    db = object()

    monkeypatch.setattr(auth, "ping_database", lambda: True)
    monkeypatch.setattr(auth, "get_database", lambda: db)
    monkeypatch.setattr(auth, "UserRepository", FakeUserRepository)

    result_db, user = auth.require_authenticated_user(allowed_roles=["learner"])

    assert result_db is db
    assert user["id"] == "user-1"
    assert user["role"] == "learner"


def test_expired_session_is_rejected_and_cleared(monkeypatch):
    expired_time = datetime.now(timezone.utc) - timedelta(
        hours=auth.settings.session_max_age_hours + 1
    )

    session = FakeSessionState(
        {
            "user": {"id": "user-1"},
            "authenticated_at": expired_time,
            "career_code": "DA",
            "last_assessment": {"score": 80},
            "ans_python": "Option A",
            "initialized": True,
            "db_ready": True,
        }
    )

    prepare_session(monkeypatch, session)

    with pytest.raises(StopExecutionError):
        auth.require_authenticated_user()

    assert "user" not in session
    assert "authenticated_at" not in session
    assert "career_code" not in session
    assert "last_assessment" not in session
    assert "ans_python" not in session

    assert session["initialized"] is True
    assert session["db_ready"] is True


def test_missing_timestamp_is_rejected_and_cleared(monkeypatch):
    session = FakeSessionState(
        {
            "user": {"id": "user-1"},
            "career_code": "DA",
            "ans_python": "Option A",
            "initialized": True,
        }
    )

    prepare_session(monkeypatch, session)

    with pytest.raises(StopExecutionError):
        auth.require_authenticated_user()

    assert "user" not in session
    assert "career_code" not in session
    assert "ans_python" not in session
    assert session["initialized"] is True


def test_naive_timestamp_is_rejected(monkeypatch):
    session = FakeSessionState(
        {
            "user": {"id": "user-1"},
            "authenticated_at": datetime.now(),
        }
    )

    prepare_session(monkeypatch, session)

    with pytest.raises(StopExecutionError):
        auth.require_authenticated_user()

    assert "user" not in session
    assert "authenticated_at" not in session
