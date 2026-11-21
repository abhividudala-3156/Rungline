import pytest
from bson import ObjectId

from database.repositories.user_repository import UserRepository


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

    def find_one(self, query):
        return next(
            (
                doc
                for doc in self.documents
                if all(doc.get(key) == value for key, value in query.items())
            ),
            None,
        )

    def update_one(self, query, update):
        from types import SimpleNamespace

        document = self.find_one(query)

        if document is None:
            return SimpleNamespace(matched_count=0)

        document.update(update.get("$set", {}))

        return SimpleNamespace(matched_count=1)

    def find(self, query, projection):
        documents = [
            {key: value for key, value in doc.items() if not (projection.get(key) == 0)}
            for doc in self.documents
        ]
        return FakeCursor(documents)


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()


def test_by_id_returns_existing_user():
    db = FakeDB()
    repository = UserRepository(db)

    user_id = ObjectId()
    db.users.documents.append(
        {
            "_id": user_id,
            "name": "Test User",
            "email": "test@example.com",
        }
    )

    result = repository.by_id(str(user_id))

    assert result is not None
    assert result["name"] == "Test User"


def test_by_id_returns_none_for_invalid_id():
    db = FakeDB()
    repository = UserRepository(db)

    assert repository.by_id("invalid-id") is None


def test_by_id_returns_none_for_non_string_id():
    db = FakeDB()
    repository = UserRepository(db)

    assert repository.by_id(None) is None


def test_list_users_excludes_password_hash():
    db = FakeDB()
    repository = UserRepository(db)

    db.users.documents.append(
        {
            "name": "Test User",
            "password_hash": "secret-hash",
        }
    )

    users = repository.list_users()

    assert len(users) == 1
    assert "password_hash" not in users[0]


def test_list_users_respects_requested_limit():
    db = FakeDB()
    repository = UserRepository(db)

    for index in range(5):
        db.users.documents.append(
            {
                "name": f"User {index}",
                "created_at": index,
            }
        )

    assert len(repository.list_users(limit=2)) == 2


def test_list_users_caps_limit_at_200():
    db = FakeDB()
    repository = UserRepository(db)

    for index in range(205):
        db.users.documents.append(
            {
                "name": f"User {index}",
                "created_at": index,
            }
        )

    assert len(repository.list_users(limit=500)) == 200


def test_list_users_rejects_invalid_limit_type():
    db = FakeDB()
    repository = UserRepository(db)

    with pytest.raises(ValueError):
        repository.list_users(limit="all")


def test_list_users_rejects_boolean_limit():
    db = FakeDB()
    repository = UserRepository(db)

    with pytest.raises(ValueError):
        repository.list_users(limit=True)


def test_update_career_goal_updates_only_allowed_fields():
    db = FakeDB()
    repository = UserRepository(db)

    user_id = ObjectId()
    db.users.documents.append(
        {
            "_id": user_id,
            "name": "Test User",
            "role": "learner",
            "is_active": True,
            "password_hash": "protected-hash",
        }
    )

    result = repository.update_career_goal(
        str(user_id),
        "DATA_ANALYST",
    )

    user = db.users.find_one({"_id": user_id})

    assert result is True
    assert user["career_code"] == "DATA_ANALYST"
    assert user["role"] == "learner"
    assert user["is_active"] is True
    assert user["password_hash"] == "protected-hash"


def test_update_career_goal_rejects_invalid_user_id():
    db = FakeDB()
    repository = UserRepository(db)

    with pytest.raises(ValueError):
        repository.update_career_goal("invalid-id", "DATA_ANALYST")


def test_update_career_goal_rejects_empty_career_code():
    db = FakeDB()
    repository = UserRepository(db)

    with pytest.raises(ValueError):
        repository.update_career_goal(str(ObjectId()), "  ")


def test_update_career_goal_returns_false_for_missing_user():
    db = FakeDB()
    repository = UserRepository(db)

    result = repository.update_career_goal(
        str(ObjectId()),
        "DATA_ANALYST",
    )

    assert result is False
