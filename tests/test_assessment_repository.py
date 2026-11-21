import pytest

from database.repositories.assessment_repository import AssessmentRepository


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
        self.documents.append(dict(document))

        class Result:
            inserted_id = "test-id"

        return Result()

    def find(self, query):
        documents = [
            doc
            for doc in self.documents
            if all(doc.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(documents)


class FakeDB:
    def __init__(self):
        self.questions = FakeCollection()
        self.assessment_attempts = FakeCollection()


def test_save_attempt_preserves_authenticated_user_id():
    db = FakeDB()
    repository = AssessmentRepository(db)

    repository.save_attempt(
        "authenticated-user",
        "DATA_ANALYST",
        {
            "answers": [],
            "skill_scores": {"PYTHON": 80},
            "user_id": "attacker-user",
        },
    )

    saved = db.assessment_attempts.documents[0]

    assert saved["user_id"] == "authenticated-user"
    assert saved["career_code"] == "DATA_ANALYST"


def test_save_attempt_rejects_unexpected_fields():
    db = FakeDB()
    repository = AssessmentRepository(db)

    repository.save_attempt(
        "user-1",
        "DATA_ANALYST",
        {
            "answers": [],
            "skill_scores": {},
            "is_admin": True,
            "password_hash": "unexpected",
        },
    )

    saved = db.assessment_attempts.documents[0]

    assert "is_admin" not in saved
    assert "password_hash" not in saved


def test_save_attempt_preserves_server_timestamp():
    db = FakeDB()
    repository = AssessmentRepository(db)

    repository.save_attempt(
        "user-1",
        "DATA_ANALYST",
        {
            "answers": [],
            "created_at": "attacker-controlled-timestamp",
        },
    )

    saved = db.assessment_attempts.documents[0]

    assert saved["created_at"] != "attacker-controlled-timestamp"
    assert saved["created_at"].tzinfo is not None


def test_save_attempt_returns_inserted_id():
    db = FakeDB()
    repository = AssessmentRepository(db)

    result = repository.save_attempt(
        "user-1",
        "DATA_ANALYST",
        {
            "answers": [],
            "skill_scores": {},
            "total_attempted": 0,
            "total_questions": 15,
            "overall_score": None,
        },
    )

    assert result == "test-id"


def test_save_attempt_rejects_invalid_user_id():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="user ID"):
        repository.save_attempt("", "DATA_ANALYST", {})


def test_save_attempt_rejects_invalid_career_code():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="career code"):
        repository.save_attempt("user-1", " ", {})


def test_save_attempt_rejects_non_dictionary_result():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="dictionary"):
        repository.save_attempt("user-1", "DATA_ANALYST", [])


def test_history_returns_only_requested_users_records():
    db = FakeDB()
    repository = AssessmentRepository(db)

    db.assessment_attempts.documents.extend(
        [
            {"user_id": "user-1", "created_at": 1},
            {"user_id": "user-2", "created_at": 2},
            {"user_id": "user-1", "created_at": 3},
        ]
    )

    history = repository.history("user-1")

    assert len(history) == 2
    assert all(item["user_id"] == "user-1" for item in history)


def test_history_caps_limit_at_200():
    db = FakeDB()
    repository = AssessmentRepository(db)

    db.assessment_attempts.documents.extend(
        {"user_id": "user-1", "created_at": index} for index in range(205)
    )

    assert len(repository.history("user-1", limit=500)) == 200


def test_history_rejects_invalid_limit():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="integer"):
        repository.history("user-1", limit="all")


def test_history_rejects_boolean_limit():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="integer"):
        repository.history("user-1", limit=True)


def test_history_rejects_empty_user_id():
    repository = AssessmentRepository(FakeDB())

    with pytest.raises(ValueError, match="user ID"):
        repository.history("")
