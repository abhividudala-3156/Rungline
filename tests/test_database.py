import os

import pytest
from pymongo import MongoClient


@pytest.mark.skipif(
    not os.getenv("TEST_MONGODB_URI"),
    reason="Set TEST_MONGODB_URI to run MongoDB integration test.",
)
def test_mongodb_ping():
    client = MongoClient(os.environ["TEST_MONGODB_URI"], serverSelectionTimeoutMS=3000)
    assert client.admin.command("ping")["ok"] == 1
    client.close()
