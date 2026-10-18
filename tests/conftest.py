import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test.db")
    conn = db.connect(path)
    db.init_db(conn)
    conn.close()
    return path


@pytest.fixture
def conn(db_path: str) -> Iterator[sqlite3.Connection]:
    connection = db.connect(db_path)
    yield connection
    connection.close()


@pytest.fixture
def client(db_path: str) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[sqlite3.Connection]:
        connection = db.connect(db_path)
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[db.get_db] = override_get_db
    # No context manager: the lifespan (which would touch dev.db) is not run.
    yield TestClient(app)
    app.dependency_overrides.clear()
