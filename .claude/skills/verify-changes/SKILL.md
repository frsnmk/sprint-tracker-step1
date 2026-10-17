---
name: verify-changes
description: Verify code changes before reporting a task as done. Use after implementing or modifying a feature, fixing a bug, or when asked to check, verify, or review recent changes in this repo.
---

# Verify changes

Do these steps in order. Do not report a task as done until step 4 is written.

1. Run `bash .claude/skills/verify-changes/check.sh`. It runs the tests, lists changed files, and flags weakened tests.
2. Read the actual diff with `git diff HEAD` (and `git status` for new files). Do not rely on your own memory of what you changed.
3. If check.sh flags a test change (removed assertion, skip/xfail, deleted test), stop. Explain why it is justified, or restore the test and fix the code. See reference.md for what counts as weakening.
4. Report with evidence, in this format:
   - Tests: the pytest summary line, copied from the output.
   - Files changed: from `git diff --stat`.
   - Test changes: none / list and justify.
   - Not verified: anything you could not check.

Never write "all tests pass" without the pytest output from this run.
