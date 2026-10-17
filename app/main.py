from fastapi import FastAPI
from pydantic import BaseModel

from app.config import APP_VERSION

app = FastAPI(title="Sprint Tracker", version=APP_VERSION)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)
