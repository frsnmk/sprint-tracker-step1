# What counts as weakening a test

Treat each of these as a red flag that needs an explicit justification:

1. A removed or loosened `assert` (for example `== 5` changed to `is not None`).
2. A new `@pytest.mark.skip`, `skipif`, `xfail`, or `pytest.skip(`.
3. A deleted test function or test file.
4. An expected value edited to match new (possibly wrong) output.
5. A new `try/except` or `pytest.raises(Exception)` that swallows failures.

Passing tests prove only that existing tests pass. Check also that the new behavior has its own tests (one success, one failure per endpoint, per CLAUDE.md).
