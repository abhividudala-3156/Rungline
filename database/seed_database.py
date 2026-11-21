import json
from datetime import datetime, timezone
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"


def _load(name):
    with (SEED_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def seed_database(db):
    """Insert missing reference records without modifying existing records."""
    specs = [
        ("careers.json", "careers", ("code",)),
        ("competencies.json", "competencies", ("code",)),
        (
            "career_competencies.json",
            "career_competencies",
            ("career_code", "competency_code"),
        ),
        ("questions.json", "questions", ("code",)),
        ("resources.json", "learning_resources", ("code",)),
    ]

    validated_data = []

    # Validate every seed file before writing to the database.
    for filename, collection, key_fields in specs:
        records = _load(filename)

        if not isinstance(records, list):
            raise ValueError(f"{filename} must contain a JSON list.")

        seen_keys = set()

        for index, item in enumerate(records):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{filename}: record {index + 1} must be a JSON object."
                )

            key_values = tuple(item.get(field) for field in key_fields)

            if any(
                not isinstance(value, str) or not value.strip() for value in key_values
            ):
                raise ValueError(
                    f"{filename}: record {index + 1} has a missing or invalid key."
                )

            if key_values in seen_keys:
                raise ValueError(
                    f"{filename}: duplicate seed key found in record {index + 1}."
                )

            seen_keys.add(key_values)

        validated_data.append((collection, key_fields, records))

    # Insert missing records only. Existing documents remain unchanged.
    now = datetime.now(timezone.utc)

    for collection, key_fields, records in validated_data:
        for item in records:
            query = {field: item[field] for field in key_fields}

            document = {
                field: value for field, value in item.items() if field != "created_at"
            }
            document["created_at"] = now

            db[collection].update_one(
                query,
                {"$setOnInsert": document},
                upsert=True,
            )

    return True
