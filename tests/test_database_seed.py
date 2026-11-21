import json
from datetime import datetime, timezone

import pytest

from database import seed_database as seed_module


class FakeCollection:
    def __init__(self):
        self.docs = []

    def update_one(self, query, update, upsert=False):
        existing = next(
            (
                doc
                for doc in self.docs
                if all(doc.get(key) == value for key, value in query.items())
            ),
            None,
        )

        if existing:
            existing.update(update.get("$set", {}))
            return

        if upsert:
            doc = dict(query)
            doc.update(update.get("$setOnInsert", {}))
            doc.update(update.get("$set", {}))
            self.docs.append(doc)


class FakeDB:
    def __init__(self):
        self.collections = {
            name: FakeCollection()
            for name in [
                "careers",
                "competencies",
                "career_competencies",
                "questions",
                "learning_resources",
            ]
        }

    def __getitem__(self, name):
        return self.collections[name]


def create_seed_files(directory):
    seed_data = {
        "careers.json": [
            {
                "code": "TEST_CAREER",
                "title": "Test Career",
                "description": "Test description",
                "is_active": True,
            }
        ],
        "competencies.json": [
            {
                "code": "TEST_SKILL",
                "name": "Test Skill",
                "category": "Testing",
            }
        ],
        "career_competencies.json": [
            {
                "career_code": "TEST_CAREER",
                "competency_code": "TEST_SKILL",
                "required_level": 3,
                "weight": 1.0,
            }
        ],
        "questions.json": [
            {
                "code": "TEST_Q1",
                "career_code": "TEST_CAREER",
                "competency_code": "TEST_SKILL",
                "prompt": "Test question?",
            }
        ],
        "resources.json": [
            {
                "code": "TEST_RES",
                "competency_code": "TEST_SKILL",
                "title": "Test Resource",
                "url": "https://example.com",
            }
        ],
    }

    for filename, records in seed_data.items():
        (directory / filename).write_text(
            json.dumps(records),
            encoding="utf-8",
        )


def test_seed_database_inserts_reference_records(tmp_path, monkeypatch):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)
    db = FakeDB()

    assert seed_module.seed_database(db) is True

    assert len(db["careers"].docs) == 1
    assert len(db["competencies"].docs) == 1
    assert len(db["career_competencies"].docs) == 1
    assert len(db["questions"].docs) == 1
    assert len(db["learning_resources"].docs) == 1


def test_seed_database_does_not_create_duplicates(tmp_path, monkeypatch):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)
    db = FakeDB()

    seed_module.seed_database(db)
    seed_module.seed_database(db)

    for collection in db.collections.values():
        assert len(collection.docs) == 1


def test_seed_database_preserves_existing_records(tmp_path, monkeypatch):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)
    db = FakeDB()

    original_timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)

    existing_career = {
        "code": "TEST_CAREER",
        "title": "Administrator Edited Title",
        "description": "Administrator edited description",
        "is_active": False,
        "custom_field": "Preserve this value",
        "created_at": original_timestamp,
    }

    db["careers"].docs.append(existing_career.copy())

    seed_module.seed_database(db)

    career = db["careers"].docs[0]

    assert career == existing_career
    assert career["created_at"] == original_timestamp


def test_seed_database_does_not_overwrite_changed_seed_fields(
    tmp_path,
    monkeypatch,
):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)
    db = FakeDB()

    seed_module.seed_database(db)

    seed_file = tmp_path / "careers.json"
    careers = json.loads(seed_file.read_text(encoding="utf-8"))
    careers[0]["title"] = "Updated Test Career"
    seed_file.write_text(json.dumps(careers), encoding="utf-8")

    seed_module.seed_database(db)

    assert len(db["careers"].docs) == 1
    assert db["careers"].docs[0]["title"] == "Test Career"


def test_seed_database_rejects_invalid_file_before_writing(
    tmp_path,
    monkeypatch,
):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)

    invalid_file = tmp_path / "resources.json"
    invalid_file.write_text('{"invalid": true}', encoding="utf-8")

    db = FakeDB()

    with pytest.raises(ValueError, match="must contain a JSON list"):
        seed_module.seed_database(db)

    for collection in db.collections.values():
        assert collection.docs == []


def test_seed_database_rejects_duplicate_seed_keys(tmp_path, monkeypatch):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)

    seed_file = tmp_path / "careers.json"
    records = json.loads(seed_file.read_text(encoding="utf-8"))
    records.append(records[0].copy())
    seed_file.write_text(json.dumps(records), encoding="utf-8")

    db = FakeDB()

    with pytest.raises(ValueError, match="duplicate seed key"):
        seed_module.seed_database(db)

    for collection in db.collections.values():
        assert collection.docs == []


def test_seed_database_rejects_missing_key_before_writing(
    tmp_path,
    monkeypatch,
):
    create_seed_files(tmp_path)
    monkeypatch.setattr(seed_module, "SEED_DIR", tmp_path)

    seed_file = tmp_path / "careers.json"
    seed_file.write_text(
        json.dumps([{"title": "Missing career code"}]),
        encoding="utf-8",
    )

    db = FakeDB()

    with pytest.raises(ValueError, match="missing or invalid key"):
        seed_module.seed_database(db)

    for collection in db.collections.values():
        assert collection.docs == []
