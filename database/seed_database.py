import json
from datetime import datetime, timezone
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"


def _load(name):
    with (SEED_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def seed_database(db):
    """Upsert reference data while preserving original creation timestamps."""
    specs = [
        ("careers.json", "careers", "code"),
        ("competencies.json", "competencies", "code"),
        ("career_competencies.json", "career_competencies", None),
        ("questions.json", "questions", "code"),
        ("resources.json", "learning_resources", "code"),
    ]

    for filename, collection, key in specs:
        for item in _load(filename):
            if key:
                query = {key: item[key]}
            else:
                query = {
                    "career_code": item["career_code"],
                    "competency_code": item["competency_code"],
                }

            update_fields = {
                field: value for field, value in item.items() if field != "created_at"
            }

            db[collection].update_one(
                query,
                {
                    "$set": update_fields,
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )

    return True
