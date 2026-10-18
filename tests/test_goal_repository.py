import sqlite3
from datetime import date

from app.repositories import goal_repository as repo
from app.schemas.goal import GoalCreate, GoalStatus, GoalUpdate


def test_create_and_get(conn: sqlite3.Connection) -> None:
    row = repo.create(conn, GoalCreate(name="Ship v1"))
    assert row["name"] == "Ship v1"
    assert row["status"] == "planned"
    assert row["created_at"] and row["updated_at"]
    assert row["deleted_at"] is None
    assert repo.get(conn, row["id"])["id"] == row["id"]


def test_get_missing_returns_none(conn: sqlite3.Connection) -> None:
    assert repo.get(conn, 999) is None


def test_update_only_changes_given_fields(conn: sqlite3.Connection) -> None:
    row = repo.create(conn, GoalCreate(name="A", description="d"))
    updated = repo.update(conn, row["id"], GoalUpdate(name="B"))
    assert updated["name"] == "B"
    assert updated["description"] == "d"


def test_update_missing_returns_none(conn: sqlite3.Connection) -> None:
    assert repo.update(conn, 999, GoalUpdate(name="B")) is None


def test_soft_delete_keeps_row(conn: sqlite3.Connection) -> None:
    row = repo.create(conn, GoalCreate(name="A"))
    assert repo.soft_delete(conn, row["id"]) is True
    assert repo.get(conn, row["id"]) is None
    kept = repo.get(conn, row["id"], include_deleted=True)
    assert kept is not None and kept["deleted_at"] is not None
    assert repo.soft_delete(conn, row["id"]) is False


def test_list_filters(conn: sqlite3.Connection) -> None:
    repo.create(conn, GoalCreate(name="Alpha", status=GoalStatus.ACTIVE, start_date=date(2026, 1, 1)))
    repo.create(conn, GoalCreate(name="Beta", status=GoalStatus.DONE, start_date=date(2026, 6, 1)))
    rows, total = repo.list_goals(conn, status=GoalStatus.ACTIVE)
    assert [r["name"] for r in rows] == ["Alpha"] and total == 1
    rows, _ = repo.list_goals(conn, q="bet")
    assert [r["name"] for r in rows] == ["Beta"]
    rows, _ = repo.list_goals(conn, start_from=date(2026, 3, 1))
    assert [r["name"] for r in rows] == ["Beta"]


def test_list_q_is_not_sql_injectable(conn: sqlite3.Connection) -> None:
    repo.create(conn, GoalCreate(name="Alpha"))
    rows, total = repo.list_goals(conn, q="'; DROP TABLE goals;--")
    assert rows == [] and total == 0
    assert repo.list_goals(conn)[1] == 1


def test_list_q_wildcards_are_literal(conn: sqlite3.Connection) -> None:
    repo.create(conn, GoalCreate(name="Alpha"))
    rows, _ = repo.list_goals(conn, q="%")
    assert rows == []
