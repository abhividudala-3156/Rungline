from types import SimpleNamespace

from database.indexes import ensure_indexes


class FakeCollection:
    def __init__(self):
        self.indexes = []

    def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))


def create_fake_db():
    names = [
        "users",
        "careers",
        "competencies",
        "career_competencies",
        "questions",
        "assessment_attempts",
        "competency_profiles",
        "learning_paths",
        "learning_progress",
        "learning_resources",
        "notifications",
        "ai_interactions",
        "audit_logs",
    ]

    collections = {name: FakeCollection() for name in names}

    return SimpleNamespace(**collections)


def test_ensure_indexes_creates_user_email_unique_index():
    db = create_fake_db()

    ensure_indexes(db)

    assert ("email", {"unique": True}) in db.users.indexes


def test_ensure_indexes_creates_unique_reference_indexes():
    db = create_fake_db()

    ensure_indexes(db)

    assert ("code", {"unique": True}) in db.careers.indexes
    assert ("code", {"unique": True}) in db.competencies.indexes


def test_ensure_indexes_creates_unique_relationship_indexes():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        [("career_code", 1), ("competency_code", 1)],
        {"unique": True},
    ) in db.career_competencies.indexes

    assert (
        [("user_id", 1), ("career_code", 1)],
        {"unique": True},
    ) in db.competency_profiles.indexes

    assert (
        [("user_id", 1), ("resource_id", 1)],
        {"unique": True},
    ) in db.learning_progress.indexes


def test_ensure_indexes_creates_user_history_index():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        [("user_id", 1), ("created_at", -1)],
        {},
    ) in db.assessment_attempts.indexes


def test_ensure_indexes_creates_learning_and_notification_indexes():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        [("user_id", 1), ("created_at", -1)],
        {},
    ) in db.learning_paths.indexes

    assert (
        [("user_id", 1), ("created_at", -1)],
        {},
    ) in db.notifications.indexes


def test_ensure_indexes_does_not_create_unused_ai_log_index():
    db = create_fake_db()

    ensure_indexes(db)

    assert db.ai_interactions.indexes == []


def test_ensure_indexes_creates_question_query_index():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        [
            ("career_code", 1),
            ("is_active", 1),
            ("competency_code", 1),
        ],
        {},
    ) in db.questions.indexes


def test_ensure_indexes_creates_audit_log_indexes():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        [("actor_id", 1), ("created_at", -1)],
        {},
    ) in db.audit_logs.indexes

    assert (
        [("created_at", -1)],
        {},
    ) in db.audit_logs.indexes


def test_ensure_indexes_creates_single_administrator_constraint():
    db = create_fake_db()

    ensure_indexes(db)

    assert (
        "role",
        {
            "unique": True,
            "partialFilterExpression": {"role": "admin"},
            "name": "one_administrator_only",
        },
    ) in db.users.indexes
