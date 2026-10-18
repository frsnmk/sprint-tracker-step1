from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app import config, db
from app.config import APP_VERSION
from app.routers import goals


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    conn = db.connect(db.database_path(config.DATABASE_URL))
    try:
        db.init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Sprint Tracker", version=APP_VERSION, lifespan=lifespan)
app.include_router(goals.router)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)
