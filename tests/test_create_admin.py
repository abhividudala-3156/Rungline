import scripts.create_admin as create_admin


class FakeUsers:
    def __init__(self, admin_count=0):
        self.admin_count = admin_count

    def count_documents(self, query):
        assert query == {"role": "admin"}
        return self.admin_count


class FakeDB:
    def __init__(self, admin_count=0):
        self.users = FakeUsers(admin_count)


def prepare_environment(monkeypatch, db):
    monkeypatch.setattr(create_admin, "ping_database", lambda: True)
    monkeypatch.setattr(create_admin, "get_database", lambda: db)
    monkeypatch.setattr(create_admin, "ensure_indexes", lambda database: None)
    monkeypatch.setattr(create_admin, "close_connection", lambda: None)


def test_existing_admin_prevents_bootstrap(monkeypatch, capsys):
    db = FakeDB(admin_count=1)
    prepare_environment(monkeypatch, db)

    result = create_admin.main()

    assert result == 1
    assert "An administrator already exists" in capsys.readouterr().out


def test_unavailable_database_stops_bootstrap(monkeypatch, capsys):
    monkeypatch.setattr(create_admin, "ping_database", lambda: False)
    monkeypatch.setattr(create_admin, "close_connection", lambda: None)

    result = create_admin.main()

    assert result == 1
    assert "MongoDB is unavailable" in capsys.readouterr().out


def test_password_mismatch_prevents_bootstrap(monkeypatch, capsys):
    db = FakeDB()
    prepare_environment(monkeypatch, db)

    monkeypatch.setattr("builtins.input", lambda prompt: "admin@example.com")
    passwords = iter(["AdminPass123", "DifferentPass123"])
    monkeypatch.setattr(
        create_admin,
        "getpass",
        lambda prompt: next(passwords),
    )

    result = create_admin.main()

    assert result == 1
    assert "Passwords do not match" in capsys.readouterr().out


def test_successful_bootstrap_records_audit(monkeypatch, capsys):
    db = FakeDB()
    prepare_environment(monkeypatch, db)

    monkeypatch.setattr("builtins.input", lambda prompt: "admin@example.com")
    monkeypatch.setattr(create_admin, "getpass", lambda prompt: "AdminPass123")

    class FakeAuthService:
        def __init__(self, database):
            assert database is db

        def bootstrap_initial_admin(self, email, password):
            assert email == "admin@example.com"
            assert password == "AdminPass123"
            return "admin-id"

    recorded = {}

    class FakeAuditRepository:
        def __init__(self, database):
            assert database is db

        def record(self, **kwargs):
            recorded.update(kwargs)
            return "audit-id"

    monkeypatch.setattr(create_admin, "AuthService", FakeAuthService)
    monkeypatch.setattr(
        create_admin,
        "AuditLogRepository",
        FakeAuditRepository,
    )

    result = create_admin.main()

    assert result == 0
    assert recorded["action"] == "auth.initial_admin.bootstrap"
    assert recorded["outcome"] == "success"
    assert recorded["actor"]["role"] == "admin"
    assert recorded["details"]["operation"] == "initial_admin_bootstrap"
    assert "Administrator account created successfully" in capsys.readouterr().out


def test_audit_failure_reports_created_account(monkeypatch, capsys):
    db = FakeDB()
    prepare_environment(monkeypatch, db)

    monkeypatch.setattr("builtins.input", lambda prompt: "admin@example.com")
    monkeypatch.setattr(create_admin, "getpass", lambda prompt: "AdminPass123")

    class FakeAuthService:
        def __init__(self, database):
            pass

        def bootstrap_initial_admin(self, email, password):
            return "admin-id"

    class FakeAuditRepository:
        def __init__(self, database):
            pass

        def record(self, **kwargs):
            raise ValueError("Audit storage unavailable")

    monkeypatch.setattr(create_admin, "AuthService", FakeAuthService)
    monkeypatch.setattr(
        create_admin,
        "AuditLogRepository",
        FakeAuditRepository,
    )

    result = create_admin.main()
    output = capsys.readouterr().out

    assert result == 1
    assert "Administrator account was created" in output
    assert "audit record could not be saved" in output
