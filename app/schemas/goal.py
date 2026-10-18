from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class GoalStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    DONE = "done"


def _clean_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("name must not be blank")
    return value


class GoalCreate(BaseModel):
    name: str
    description: str | None = None
    status: GoalStatus | None = GoalStatus.PLANNED
    start_date: date | None = None
    end_date: date | None = None

    _check_name = field_validator("name")(_clean_name)

    @model_validator(mode="after")
    def _check_dates(self) -> "GoalCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class GoalUpdate(BaseModel):
    """Partial update. Fields that are omitted stay unchanged; explicit null clears nullable fields."""

    name: str | None = None
    description: str | None = None
    status: GoalStatus | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _check(self) -> "GoalUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if "name" in self.model_fields_set:
            if self.name is None:
                raise ValueError("name must not be null")
            self.name = _clean_name(self.name)
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: GoalStatus | None
    start_date: date | None
    end_date: date | None
    created_at: str | None
    updated_at: str | None
    deleted_at: str | None


class GoalListResponse(BaseModel):
    items: list[GoalResponse]
    total: int
    limit: int
    offset: int
