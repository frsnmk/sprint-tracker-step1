#!/usr/bin/env python3
"""Stop hook: refuse to end the turn while the test suite fails.

Exit 0 = let Claude stop. Exit 2 = keep Claude working (stderr goes to Claude).
Safety valve: after MAX_BLOCKS consecutive failures in one session, allow the stop
so a test Claude cannot fix does not trap the session in an endless loop.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BLOCKS = 3
TAIL_LINES = 60


def counter_path(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"
    return Path(tempfile.gettempdir()) / f"sprint-tracker-stop-{safe}.count"


def read_count(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return 0


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    counter = counter_path(str(data.get("session_id", "")))

    venv_pytest = project / ".venv" / "bin" / "pytest"
    cmd = [str(venv_pytest), "-q"] if venv_pytest.exists() else [sys.executable, "-m", "pytest", "-q"]

    try:
        result = subprocess.run(
            cmd, cwd=project, capture_output=True, text=True, timeout=240
        )
        output = (result.stdout + result.stderr).strip()
        code = result.returncode
    except subprocess.TimeoutExpired:
        output, code = "pytest timed out after 240 seconds.", 1
    except OSError as exc:
        output, code = f"Could not run pytest: {exc}", 1

    if code == 0:
        counter.unlink(missing_ok=True)
        return 0

    blocks = read_count(counter) + 1
    if blocks > MAX_BLOCKS:
        counter.unlink(missing_ok=True)
        print(
            f"Tests still failing after {MAX_BLOCKS} attempts; allowing stop. "
            "Review the failures yourself.",
            file=sys.stderr,
        )
        return 0

    counter.write_text(str(blocks))
    tail = "\n".join(output.splitlines()[-TAIL_LINES:])
    print(
        f"Tests are failing (attempt {blocks}/{MAX_BLOCKS}). "
        f"Fix the code, do not weaken the tests.\n\n{tail}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
