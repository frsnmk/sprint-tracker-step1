# Sprint Tracker

Goal and sprint tracker built with FastAPI and SQLite.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/health or http://127.0.0.1:8000/docs.

## Test

```bash
pytest -q
```
