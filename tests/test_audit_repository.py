from datetime import datetime, timedelta, timezone

import pytest

from database.repositories.audit_repository import AuditLogRepository


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(
            key=lambda doc: doc.get(field),
            reverse=direction == -1,
        )
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        from types import SimpleNamespace

        stored = dict(document)
        stored["_id"] = str(len(self.documents) + 1)
        self.documents.append(stored)

        return SimpleNamespace(inserted_id=stored["_id"])

    def find(self, query):
        documents = [
            doc
            for doc in self.documents
            if all(doc.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(documents)


class FakeDB:
    def __init__(self):
        self.audit_logs = FakeCollection()


@pytest.fixture
def setup_repository():
    db = FakeDB()
    repository = AuditLogRepository(db)

    actor = {
        "id": "admin-123",
        "email": "ADMIN@example.com",
        "role": "admin",
    }

    return db, repository, actor


def test_record_creates_audit_log(setup_repository):
    db, repository, actor = setup_repository

    log_id = repository.record(
        actor=actor,
        action="database.indexes.ensure",
        outcome="success",
        target_type="database",
        target_id="competency_learning_db",
        details={"operation": "ensure_indexes"},
    )

    assert log_id == "1"
    assert len(db.audit_logs.documents) == 1


def test_record_normalizes_actor_email(setup_repository):
    db, repository, actor = setup_repository

    repository.record(actor, "database.seed.update", "success")

    assert db.audit_logs.documents[0]["actor_email"] == "admin@example.com"


def test_record_uses_utc_timestamp(setup_repository):
    db, repository, actor = setup_repository

    repository.record(actor, "database.indexes.ensure", "success")

    timestamp = db.audit_logs.documents[0]["created_at"]

    assert isinstance(timestamp, datetime)
    assert timestamp.tzinfo == timezone.utc


def test_record_rejects_non_admin_actor(setup_repository):
    _, repository, actor = setup_repository
    actor["role"] = "learner"

    with pytest.raises(ValueError, match="Only administrators"):
        repository.record(actor, "database.indexes.ensure", "success")


def test_record_rejects_incomplete_actor(setup_repository):
    _, repository, _ = setup_repository

    with pytest.raises(ValueError, match="Actor identity"):
        repository.record(
            {"id": "admin-123", "role": "admin"},
            "database.indexes.ensure",
            "success",
        )


def test_record_rejects_unsupported_action(setup_repository):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="Unsupported audit action"):
        repository.record(actor, "users.delete", "success")


def test_record_rejects_invalid_outcome(setup_repository):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="Invalid audit outcome"):
        repository.record(actor, "database.indexes.ensure", "pending")


def test_record_rejects_unsupported_metadata(setup_repository):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="unsupported fields"):
        repository.record(
            actor,
            "database.indexes.ensure",
            "success",
            details={"password": "secret"},
        )


def test_record_rejects_invalid_count(setup_repository):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="count must be an integer"):
        repository.record(
            actor,
            "database.seed.update",
            "success",
            details={"count": True},
        )


def test_list_recent_returns_newest_first(setup_repository):
    db, repository, actor = setup_repository

    repository.record(actor, "database.indexes.ensure", "success")
    repository.record(actor, "database.seed.update", "success")

    now = datetime.now(timezone.utc)

    db.audit_logs.documents[0]["created_at"] = now - timedelta(minutes=1)
    db.audit_logs.documents[1]["created_at"] = now

    logs = repository.list_recent(actor)

    assert len(logs) == 2
    assert logs[0]["action"] == "database.seed.update"
    assert logs[1]["action"] == "database.indexes.ensure"


def test_list_recent_caps_results_at_200(setup_repository):
    _, repository, actor = setup_repository

    for _ in range(205):
        repository.record(actor, "database.indexes.ensure", "success")

    assert len(repository.list_recent(actor, limit=500)) == 200


def test_list_recent_rejects_invalid_limit(setup_repository):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="integer"):
        repository.list_recent(actor, limit="all")


def test_repository_has_no_update_or_delete_methods(setup_repository):
    _, repository, _ = setup_repository

    assert not hasattr(repository, "update")
    assert not hasattr(repository, "delete")


def test_list_recent_rejects_learner(setup_repository):
    _, repository, actor = setup_repository
    actor["role"] = "learner"

    with pytest.raises(ValueError, match="Only administrators"):
        repository.list_recent(actor)


def test_list_recent_rejects_incomplete_admin(setup_repository):
    _, repository, _ = setup_repository

    with pytest.raises(ValueError, match="identity is incomplete"):
        repository.list_recent({"id": "admin-123", "role": "admin"})


def test_record_initial_admin_bootstrap(setup_repository):
    db, repository, actor = setup_repository

    log_id = repository.record(
        actor=actor,
        action="auth.initial_admin.bootstrap",
        outcome="success",
        target_type="platform",
        details={"operation": "initial_admin_bootstrap"},
    )

    assert log_id == "1"
    assert len(db.audit_logs.documents) == 1

    log = db.audit_logs.documents[0]

    assert log["action"] == "auth.initial_admin.bootstrap"
    assert log["outcome"] == "success"
    assert log["details"]["operation"] == "initial_admin_bootstrap"


def test_record_initial_admin_bootstrap_rejects_password_metadata(
    setup_repository,
):
    _, repository, actor = setup_repository

    with pytest.raises(ValueError, match="unsupported fields"):
        repository.record(
            actor=actor,
            action="auth.initial_admin.bootstrap",
            outcome="success",
            details={
                "operation": "initial_admin_bootstrap",
                "password": "must-not-be-stored",
            },
        )
