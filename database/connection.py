
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


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
        logger.warning(
            "MongoDB health check failed (%s).",
            type(exc).__name__,
        )
        return False


def close_connection() -> None:
    if get_client.cache_info().currsize:
        get_client().close()
        get_client.cache_clear()
