# Sprint Tracker

FastAPI + SQLite goal and sprint tracker. Goal contains Sprints, Sprint contains Tasks.

## Commands

- Install: `pip install -r requirements.txt` (inside `.venv`)
- Run tests: `pytest -q`
- Run server: `uvicorn app.main:app --reload`

## Structure

- `app/main.py`: creates the FastAPI app and registers routers.
- `app/config.py`: settings; `DATABASE_URL` is read from the environment.
- `app/routers/`: one router per file.
- `tests/`: one test file per module, named `test_<module>.py`.

## Conventions

- Put new API routes in `app/routers/`, one router per file, registered in `app/main.py`.
- Use Pydantic models for request and response bodies, not raw dicts.
- Add type hints to every function signature.
- Every new endpoint gets at least one success test and one failure test in `tests/`.
- Tests use a temporary SQLite database, not `dev.db`.
- Run `pytest -q` and show its output before saying a task is done.

## Hard rules

- IMPORTANT: Never edit or delete an existing test to make it pass. Fix the code, or ask first.
- IMPORTANT: Only use local SQLite files. Never connect to any other database.
