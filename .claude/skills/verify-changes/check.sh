#!/usr/bin/env bash
# Verification gate. Exit 0 = ok, 1 = tests failed, 3 = weakened tests suspected.
# Usage: check.sh [base-ref]   (default: HEAD, i.e. all uncommitted changes)
set -u
BASE="${1:-HEAD}"
cd "$(git rev-parse --show-toplevel)" || exit 1

if [ -x .venv/bin/pytest ]; then PYTEST=".venv/bin/pytest"; else PYTEST="python3 -m pytest"; fi

echo "== 1. Tests =="
$PYTEST -q
TEST_RC=$?

echo
echo "== 2. Changed files vs $BASE =="
git status --short
git diff --stat "$BASE" 2>/dev/null

echo
echo "== 3. Test-weakening scan =="
WARN=0
# Deleted test files
DELETED=$(git diff --name-status "$BASE" -- tests 2>/dev/null | awk '$1=="D"{print $2}')
if [ -n "$DELETED" ]; then echo "WARN deleted test files:"; echo "$DELETED"; WARN=1; fi
# Removed assert lines, or newly added skip/xfail
REMOVED=$(git diff -U0 "$BASE" -- tests 2>/dev/null | grep -E '^-[^-].*\bassert\b' || true)
if [ -n "$REMOVED" ]; then echo "WARN removed assert lines:"; echo "$REMOVED"; WARN=1; fi
SKIPS=$(git diff -U0 "$BASE" -- tests 2>/dev/null | grep -E '^\+[^+].*(mark\.skip|skipif|xfail|pytest\.skip\()' || true)
if [ -n "$SKIPS" ]; then echo "WARN added skip/xfail:"; echo "$SKIPS"; WARN=1; fi
[ "$WARN" -eq 0 ] && echo "none found"

echo
if [ "$TEST_RC" -ne 0 ]; then echo "RESULT: tests FAILED"; exit 1; fi
if [ "$WARN" -ne 0 ]; then echo "RESULT: tests pass but test changes need justification"; exit 3; fi
echo "RESULT: ok"
exit 0
