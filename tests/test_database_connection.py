import logging

from database import connection


class FakeAdmin:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def command(self, command):
        if self.should_fail:
            raise connection.PyMongoError("Database unavailable.")

        return {"ok": 1}


class FakeClient:
    def __init__(self, should_fail=False):
        self.admin = FakeAdmin(should_fail)
        self.closed = False

    def close(self):
        self.closed = True


def test_get_client_reuses_cached_connection(monkeypatch):
    connection.get_client.cache_clear()
    clients = []

    def fake_client(*args, **kwargs):
        client = FakeClient()
        clients.append(client)
        return client

    monkeypatch.setattr(connection, "MongoClient", fake_client)

    first = connection.get_client()
    second = connection.get_client()

    assert first is second
    assert len(clients) == 1

    connection.get_client.cache_clear()


def test_ping_database_returns_true(monkeypatch):
    monkeypatch.setattr(
        connection,
        "get_client",
        lambda: FakeClient(),
    )

    assert connection.ping_database() is True


def test_ping_database_handles_connection_failure(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(
        connection,
        "get_client",
        lambda: FakeClient(should_fail=True),
    )

    with caplog.at_level(logging.WARNING):
        result = connection.ping_database()

    assert result is False
    assert "MongoDB health check failed" in caplog.text


def test_close_connection_closes_cached_client(monkeypatch):
    connection.get_client.cache_clear()
    client = FakeClient()

    monkeypatch.setattr(
        connection,
        "MongoClient",
        lambda *args, **kwargs: client,
    )

    connection.get_client()

    connection.close_connection()

    assert client.closed is True
    assert connection.get_client.cache_info().currsize == 0
