import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from app.schemas.goal import GoalCreate, GoalStatus, GoalUpdate


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _enum(value: GoalStatus | None) -> str | None:
    return value.value if value else None


def get(conn: sqlite3.Connection, goal_id: int, include_deleted: bool = False) -> sqlite3.Row | None:
    sql = "SELECT * FROM goals WHERE id = ?"
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    return conn.execute(sql, (goal_id,)).fetchone()


def create(conn: sqlite3.Connection, data: GoalCreate) -> sqlite3.Row:
    now = _now()
    cur = conn.execute(
        "INSERT INTO goals (name, description, status, start_date, end_date, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data.name, data.description, _enum(data.status), _iso(data.start_date), _iso(data.end_date), now, now),
    )
    conn.commit()
    row = get(conn, int(cur.lastrowid))
    assert row is not None
    return row


def list_goals(
    conn: sqlite3.Connection,
    *,
    status: GoalStatus | None = None,
    q: str | None = None,
    start_from: date | None = None,
    start_to: date | None = None,
    end_from: date | None = None,
    end_to: date | None = None,
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[sqlite3.Row], int]:
    clauses: list[str] = []
    params: list[Any] = []
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if status is not None:
        clauses.append("status = ?")
        params.append(status.value)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append("name LIKE ? ESCAPE '\\' COLLATE NOCASE")
        params.append(f"%{escaped}%")
    for column, op, value in (
        ("start_date", ">=", start_from),
        ("start_date", "<=", start_to),
        ("end_date", ">=", end_from),
        ("end_date", "<=", end_to),
    ):
        if value is not None:
            clauses.append(f"{column} {op} ?")
            params.append(value.isoformat())
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM goals{where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM goals{where} ORDER BY id LIMIT ? OFFSET ?", [*params, limit, offset]
    ).fetchall()
    return rows, total


def update(conn: sqlite3.Connection, goal_id: int, data: GoalUpdate) -> sqlite3.Row | None:
    current = get(conn, goal_id)
    if current is None:
        return None
    changes = data.model_dump(exclude_unset=True)
    values: dict[str, Any] = {}
    for field, value in changes.items():
        if field == "status":
            values[field] = _enum(value)
        elif field in ("start_date", "end_date"):
            values[field] = _iso(value)
        else:
            values[field] = value
    values["updated_at"] = _now()
    assignments = ", ".join(f"{column} = ?" for column in values)
    conn.execute(f"UPDATE goals SET {assignments} WHERE id = ?", [*values.values(), goal_id])
    conn.commit()
    return get(conn, goal_id)


def soft_delete(conn: sqlite3.Connection, goal_id: int) -> bool:
    now = _now()
    cur = conn.execute(
        "UPDATE goals SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
        (now, now, goal_id),
    )
    conn.commit()
    return cur.rowcount > 0
