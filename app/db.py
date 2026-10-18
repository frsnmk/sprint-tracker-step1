import sqlite3
from collections.abc import Iterator

from app import config

SQLITE_PREFIX = "sqlite:///"

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT,
    status      TEXT DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'done')),
    start_date  TEXT,
    end_date    TEXT,
    created_at  TEXT,
    updated_at  TEXT,
    deleted_at  TEXT,
    CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_deleted ON goals(deleted_at);
"""


def database_path(database_url: str) -> str:
    """Extract the SQLite file path from a sqlite:/// URL. Other schemes are rejected."""
    if not database_url.startswith(SQLITE_PREFIX):
        raise ValueError("Only local sqlite:/// database URLs are supported")
    return database_url[len(SQLITE_PREFIX):]


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    conn = connect(database_path(config.DATABASE_URL))
    try:
        yield conn
    finally:
        conn.close()
