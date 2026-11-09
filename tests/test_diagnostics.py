import app.storage as storage
from pathlib import Path

from app.diagnostics import check_tcp, host_snapshot
from app.main import health, metrics


def test_health_payload():
    assert health() == {"status": "ok", "service": "infrapilot", "version": "2.0.0"}


def test_host_snapshot_has_capacity_signals():
    result = host_snapshot()
    assert {"cpu_percent", "memory_percent", "disk_percent", "uptime_seconds", "status"} <= result.keys()
    assert 0 <= result["cpu_percent"] <= 100


def test_snapshot_round_trip(monkeypatch):
    db_path = Path("test_snapshot.db")
    db_path.unlink(missing_ok=True)
    monkeypatch.setattr(storage, "DB_PATH", str(db_path))
    try:
        saved = storage.save_snapshot({"status": "ok"})
        recent = storage.recent_snapshots()
        assert recent == [saved]
    finally:
        db_path.unlink(missing_ok=True)


def test_snapshot_round_trip_uses_mysql_when_configured(monkeypatch):
    class FakeCursor:
        lastrowid = 17

        def __init__(self, connection):
            self.connection = connection

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, query, params=None):
            self.connection.queries.append((query, params))

        def fetchall(self):
            return self.connection.rows

    class FakeConnection:
        def __init__(self):
            self.queries = []
            self.rows = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def cursor(self):
            return FakeCursor(self)

        def commit(self):
            inserted = self.queries[-1][1]
            self.rows = [{"id": 17, "created_at": inserted[0], "payload": {"status": "ok"}}]

    fake_connection = FakeConnection()
    monkeypatch.setenv("INFRAPILOT_STORAGE_BACKEND", "mysql")
    monkeypatch.setattr(storage, "_mysql_connection", lambda: fake_connection)

    saved = storage.save_snapshot({"status": "ok"})
    recent = storage.recent_snapshots()

    assert saved["id"] == 17
    assert recent == [saved]


def test_metrics_are_prometheus_text():
    assert "# TYPE infrapilot_cpu_percent gauge" in metrics()


def test_tcp_check_reports_invalid_port():
    result = check_tcp("localhost", 70000)
    assert result["reachable"] is False
    assert result["error"]
