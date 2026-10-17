#!/usr/bin/env python3
"""PreToolUse hook for Bash: block commands that break the project's hard rules.

Exit 0 = allow. Exit 2 = block (stderr is shown to Claude).
Exit 1 would NOT block, so never use it to stop a command.
"""
import json
import re
import sys

RULES = [
    (
        r"\bgit\s+push\b[^|;&]*(--force\b|--force-with-lease\b|\s-f\b)",
        "Force push is blocked. Use a normal `git push`.",
    ),
    (
        # Only when used as a command (start of line or after ; & | ( `), not when
        # the word merely appears inside text such as a commit message.
        r"(?:^|[;&|(`])\s*(?:\w+=\S+\s+)*(?:sudo\s+)?"
        r"(?:psql|pg_dump|pg_restore|mysql|mysqldump|mongosh|mongodump|redis-cli)\b",
        "Only local SQLite is allowed. Database clients for other databases are blocked.",
    ),
    (
        r"\b(postgres|postgresql|mysql|mongodb|redis)(\+\w+)?://",
        "Only local SQLite is allowed. Connection strings for other databases are blocked.",
    ),
]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # Not our input; do not get in the way.

    command = (data.get("tool_input") or {}).get("command", "")
    for pattern, message in RULES:
        if re.search(pattern, command):
            print(f"BLOCKED by project hook: {message}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
