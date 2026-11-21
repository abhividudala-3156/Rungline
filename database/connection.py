
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pymongo.uri_parser import parse_uri

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _diagnose_mongodb_uri() -> None:
    """Log safe MongoDB URI diagnostics without exposing credentials."""
    uri = settings.mongodb_uri

    logger.warning(
        "MongoDB URI diagnostics: type=%s, length=%s, "
        "has_scheme=%s, has_outer_whitespace=%s, "
        "has_newline=%s, has_quote=%s",
        type(uri).__name__,
        len(uri) if isinstance(uri, str) else 0,
        isinstance(uri, str)
        and uri.startswith(("mongodb://", "mongodb+srv://")),
        isinstance(uri, str) and uri != uri.strip(),
        isinstance(uri, str) and ("\n" in uri or "\r" in uri),
        isinstance(uri, str) and ('"' in uri or "'" in uri),
    )

    try:
        parsed = parse_uri(uri.strip())
        logger.warning(
            "MongoDB URI parsing: successful; database_present=%s; "
            "username_present=%s; host_count=%s",
            bool(parsed.get("database")),
            bool(parsed.get("username")),
            len(parsed.get("nodelist", [])),
        )
    except Exception as exc:
        logger.warning(
            "MongoDB URI parsing failed. Error type: %s",
            type(exc).__name__,
        )


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    return MongoClient(
        settings.mongodb_uri,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
    )


def get_database() -> Database:
    return get_client()[settings.database_name]


def ping_database() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except PyMongoError as exc:
        if type(exc).__name__ == "InvalidURI":
            _diagnose_mongodb_uri()

        logger.warning(
            "MongoDB health check failed (%s).",
            type(exc).__name__,
        )
        return False


def close_connection() -> None:
    if get_client.cache_info().currsize:
        get_client().close()
        get_client.cache_clear()
