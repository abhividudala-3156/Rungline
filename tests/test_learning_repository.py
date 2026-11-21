import pytest
from bson import ObjectId

from database.repositories.learning_repository import LearningRepository


class FakeCollection:
    def __init__(self):
        self.documents = []

    def find_one(self, query, sort=None):
        return next(
            (
                doc
                for doc in self.documents
                if all(doc.get(key) == value for key, value in query.items())
            ),
            None,
        )

    def update_one(self, query, update, upsert=False):
        document = self.find_one(query)

        if document is None:
            if not upsert:
                return

            document = dict(query)
            document.update(update.get("$setOnInsert", {}))
            self.documents.append(document)

        document.update(update.get("$set", {}))

    def insert_one(self, document):
        saved = dict(document)
        self.documents.append(saved)

        class Result:
            inserted_id = "test-id"

        return Result()


class FakeDB:
    def __init__(self):
        self.learning_paths = FakeCollection()
        self.learning_progress = FakeCollection()
        self.notifications = FakeCollection()
        self.ai_interactions = FakeCollection()


def create_repository():
    db = FakeDB()
    repository = LearningRepository(db)

    path_id = ObjectId()

    db.learning_paths.documents.append(
        {
            "_id": path_id,
            "user_id": "user-1",
            "career_code": "DATA_ANALYST",
            "path": {
                "steps": [
                    {"title": "Learn Python"},
                    {"title": "Learn SQL"},
                ]
            },
        }
    )

    return db, repository, path_id


# Learning path tests


def test_valid_learning_path_is_saved():
    db, repository, _ = create_repository()

    path = {
        "career_code": "DATA_ANALYST",
        "summary": "Learn data analysis.",
        "steps": [],
    }

    result = repository.save_path(
        "user-1",
        "DATA_ANALYST",
        path,
    )

    saved = db.learning_paths.documents[-1]

    assert result == "test-id"
    assert saved["user_id"] == "user-1"
    assert saved["career_code"] == "DATA_ANALYST"
    assert saved["path"] == path
    assert saved["status"] == "active"
    assert "created_at" in saved


def test_save_path_rejects_empty_user_id():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="user ID"):
        repository.save_path(
            "",
            "DATA_ANALYST",
            {"career_code": "DATA_ANALYST"},
        )


def test_save_path_rejects_empty_career_code():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="career code"):
        repository.save_path(
            "user-1",
            " ",
            {"career_code": "DATA_ANALYST"},
        )


def test_save_path_rejects_non_dictionary_path():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="dictionary"):
        repository.save_path(
            "user-1",
            "DATA_ANALYST",
            "invalid path",
        )


def test_save_path_rejects_career_code_mismatch():
    _, repository, _ = create_repository()

    path = {
        "career_code": "PYTHON_DEVELOPER",
        "summary": "Learn Python development.",
        "steps": [],
    }

    with pytest.raises(ValueError, match="does not match"):
        repository.save_path(
            "user-1",
            "DATA_ANALYST",
            path,
        )


# Learning progress tests


def test_valid_progress_is_saved():
    db, repository, path_id = create_repository()

    resource_id = f"{path_id}:1"

    repository.set_progress("user-1", resource_id, True)

    saved = db.learning_progress.documents[0]

    assert saved["user_id"] == "user-1"
    assert saved["resource_id"] == resource_id
    assert saved["completed"] is True


def test_progress_rejects_invalid_user_id():
    _, repository, path_id = create_repository()

    with pytest.raises(ValueError, match="user ID"):
        repository.set_progress("", f"{path_id}:1", True)


def test_progress_rejects_non_boolean_completion():
    _, repository, path_id = create_repository()

    with pytest.raises(ValueError, match="Boolean"):
        repository.set_progress("user-1", f"{path_id}:1", "true")


def test_progress_rejects_invalid_resource_id():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="Invalid learning resource ID"):
        repository.set_progress("user-1", "invalid-id", True)


def test_progress_rejects_another_users_roadmap():
    _, repository, path_id = create_repository()

    with pytest.raises(ValueError, match="not found for this user"):
        repository.set_progress("user-2", f"{path_id}:1", True)


def test_progress_rejects_nonexistent_step():
    _, repository, path_id = create_repository()

    with pytest.raises(ValueError, match="step does not exist"):
        repository.set_progress("user-1", f"{path_id}:10", True)


def test_progress_rejects_zero_step_number():
    _, repository, path_id = create_repository()

    with pytest.raises(ValueError, match="Invalid learning step number"):
        repository.set_progress("user-1", f"{path_id}:0", True)


def test_progress_can_be_updated():
    db, repository, path_id = create_repository()

    resource_id = f"{path_id}:1"

    repository.set_progress("user-1", resource_id, True)
    repository.set_progress("user-1", resource_id, False)

    assert len(db.learning_progress.documents) == 1
    assert db.learning_progress.documents[0]["completed"] is False


# Notification tests


def test_notification_rejects_empty_message():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="cannot be empty"):
        repository.notify("user-1", "   ")


def test_notification_rejects_invalid_kind():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="Invalid notification type"):
        repository.notify("user-1", "Assessment completed", "unknown")


@pytest.mark.parametrize(
    "kind",
    [
        [],
        {},
        None,
        123,
    ],
)
def test_notification_rejects_non_string_kind(kind):
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="Invalid notification type"):
        repository.notify("user-1", "Assessment completed", kind)


def test_notification_saves_valid_data():
    db, repository, _ = create_repository()

    repository.notify("user-1", "Assessment completed", "success")

    saved = db.notifications.documents[0]

    assert saved["user_id"] == "user-1"
    assert saved["message"] == "Assessment completed"
    assert saved["kind"] == "success"
    assert saved["read"] is False


# AI logging tests


def test_ai_log_truncates_long_summaries():
    db, repository, _ = create_repository()

    repository.log_ai(
        "user-1",
        "Learning Agent",
        "P" * 600,
        "O" * 1200,
        "success",
    )

    saved = db.ai_interactions.documents[0]

    assert saved["user_id"] == "user-1"
    assert len(saved["prompt_summary"]) == 500
    assert len(saved["output_summary"]) == 1000
    assert saved["status"] == "success"


def test_progress_for_user_rejects_empty_user_id():
    _, repository, _ = create_repository()

    with pytest.raises(ValueError, match="user ID"):
        repository.progress_for_user("")
