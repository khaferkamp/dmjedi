---
phase: 03-integration-testing
plan: "01"
subsystem: testing
tags: [uv, pytest, pytest-cov, duckdb, sqlglot]
requires:
  - phase: 02-sql-dialects
    provides: dialect-aware sql-jinja output that Phase 03 validates
provides:
  - uv-managed Phase 03 test dependencies for DuckDB and SQLGlot
  - Repo-level pytest coverage gate enforcing 85 percent total coverage
  - Task-level verification path that remains runnable with --no-cov
affects: [03-02, 03-03, testing, validation]
tech-stack:
  added: [duckdb, sqlglot]
  patterns: [repo-level pytest-cov gate via pyproject, uv run pytest as canonical verification command]
key-files:
  created: [.planning/phases/03-integration-testing/03-01-SUMMARY.md]
  modified: [pyproject.toml]
key-decisions:
  - "Kept the 85 percent coverage threshold in pytest addopts so `uv run pytest` is the canonical hard gate."
  - "Set coverage source in repo config and relied on `--no-cov` for targeted task checks instead of adding wrapper commands."
patterns-established:
  - "Phase 03 verification runs through uv-managed pytest commands, not ambient Python."
  - "Coverage enforcement lives in versioned repo config so local and future CI runs share the same threshold."
requirements-completed: [TEST-04]
duration: 4min
completed: 2026-04-17
---

# Phase 3 Plan 01: Bootstrap Test Coverage Summary

**DuckDB and SQLGlot are now part of the dev environment, and `uv run pytest` enforces an 85 percent coverage gate from repo config.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-17T05:37:00Z
- **Completed:** 2026-04-17T05:41:32Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `duckdb` and `sqlglot` to the repo dev dependency set in `pyproject.toml`.
- Turned the full-suite command into a hard-fail coverage gate with `pytest-cov` at 85 percent.
- Preserved targeted task verification by keeping `--no-cov` available for plan-level spot checks.

## Task Commits

Each task was committed atomically:

1. **Task 1: Bootstrap uv-managed Phase 03 test dependencies and coverage gate** - `3c7d93f` (chore)

## Files Created/Modified

- `pyproject.toml` - Added DuckDB and SQLGlot dev dependencies, pytest coverage addopts, and repo coverage source config.
- `.planning/phases/03-integration-testing/03-01-SUMMARY.md` - Captures execution outcome, decisions, and verification evidence for the plan.

## Decisions Made

- Kept coverage enforcement in `pyproject.toml` so `uv run pytest` is the canonical quality gate.
- Used coverage `source = ["src/dmjedi"]` with bare `--cov` in pytest config, which keeps the gate repo-managed without forcing partial runs through coverage when `--no-cov` is used.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `uv run pytest --no-cov tests/test_integration.py::test_e2e_sql_pipeline -x` initially hit a sandbox restriction on the shared uv cache path. Re-ran the exact required command with elevated permissions and it passed.
- `uv run` refreshed `uv.lock` during dependency resolution, but the plan success criteria required this bootstrap plan to leave `pyproject.toml` as the only repo file change. Reverted the incidental lockfile update before committing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 03 now has the required DuckDB and SQLGlot dev dependencies declared in repo config.
- `03-02` can add shared canonical row fixtures and DuckDB execution helpers on top of the uv-managed pytest baseline.

## Self-Check: PASSED

- Verified `.planning/phases/03-integration-testing/03-01-SUMMARY.md` exists on disk.
- Verified task commit `3c7d93f` exists in git history.

---
*Phase: 03-integration-testing*
*Completed: 2026-04-17*
