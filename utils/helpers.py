from datetime import datetime, timezone

from bson import ObjectId


def to_id(value):
    return str(value) if isinstance(value, ObjectId) else value


def utc_now():
    return datetime.now(timezone.utc)


def clean_document(doc):
    if not doc:
        return doc
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result
