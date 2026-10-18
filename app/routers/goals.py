import sqlite3
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.db import get_db
from app.repositories import goal_repository as repo
from app.schemas.goal import GoalCreate, GoalListResponse, GoalResponse, GoalStatus, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"])

Db = Annotated[sqlite3.Connection, Depends(get_db)]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(data: GoalCreate, conn: Db) -> GoalResponse:
    return GoalResponse.model_validate(dict(repo.create(conn, data)))


@router.get("", response_model=GoalListResponse)
def list_goals(
    conn: Db,
    status_filter: Annotated[GoalStatus | None, Query(alias="status")] = None,
    q: str | None = None,
    start_from: date | None = None,
    start_to: date | None = None,
    end_from: date | None = None,
    end_to: date | None = None,
    include_deleted: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GoalListResponse:
    rows, total = repo.list_goals(
        conn,
        status=status_filter,
        q=q,
        start_from=start_from,
        start_to=start_to,
        end_from=end_from,
        end_to=end_to,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    return GoalListResponse(
        items=[GoalResponse.model_validate(dict(r)) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: int, conn: Db) -> GoalResponse:
    row = repo.get(conn, goal_id)
    if row is None:
        raise _not_found()
    return GoalResponse.model_validate(dict(row))


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, data: GoalUpdate, conn: Db) -> GoalResponse:
    current = repo.get(conn, goal_id)
    if current is None:
        raise _not_found()
    # Validate the merged date range, since a patch may only carry one of the two dates.
    start = data.start_date if "start_date" in data.model_fields_set else current["start_date"]
    end = data.end_date if "end_date" in data.model_fields_set else current["end_date"]
    start_s = start.isoformat() if isinstance(start, date) else start
    end_s = end.isoformat() if isinstance(end, date) else end
    if start_s and end_s and end_s < start_s:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="end_date must not be before start_date",
        )
    row = repo.update(conn, goal_id, data)
    assert row is not None
    return GoalResponse.model_validate(dict(row))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, conn: Db) -> Response:
    if not repo.soft_delete(conn, goal_id):
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
