import sqlite3

import pytest

from app import db


def test_database_path_parses_sqlite_url() -> None:
    assert db.database_path("sqlite:///./dev.db") == "./dev.db"


def test_database_path_rejects_non_sqlite_url() -> None:
    with pytest.raises(ValueError):
        db.database_path("http://example.com/db")


def test_init_db_is_idempotent(conn: sqlite3.Connection) -> None:
    db.init_db(conn)
    db.init_db(conn)
    tables = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "goals" in tables


def test_schema_rejects_invalid_status(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO goals (name, status) VALUES ('x', 'bogus')")


def test_schema_rejects_blank_name(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO goals (name) VALUES ('   ')")


def test_get_db_yields_working_connection(db_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db.config, "DATABASE_URL", f"sqlite:///{db_path}")
    gen = db.get_db()
    connection = next(gen)
    assert connection.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0
    gen.close()
