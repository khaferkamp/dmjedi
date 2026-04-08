---
phase: 11-output-completeness
plan: "03"
subsystem: cli
tags: [typer, cli, sql-jinja, dialect, generate]

# Dependency graph
requires:
  - phase: 11-output-completeness
    provides: SqlJinjaGenerator with dialect constructor parameter
provides:
  - "--dialect CLI flag on the generate command wired to SqlJinjaGenerator(dialect=)"
  - "Allowlist validation for dialect values (default, postgres, spark)"
  - "Warning message when --dialect used with non-sql-jinja target"
affects: [cli, sql-jinja-generator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bypass registry and instantiate generator directly when constructor params are needed"
    - "Explicit BaseGenerator type annotation on gen variable for mypy compatibility"

key-files:
  created: []
  modified:
    - src/dmjedi/cli/main.py
    - tests/test_cli.py

key-decisions:
  - "Instantiate SqlJinjaGenerator directly in generate command instead of registry.get() to pass dialect (registry only stores the default instance)"
  - "Validate dialect against allowlist {'default', 'postgres', 'spark'} before use — T-11-05 mitigation"
  - "Non-sql-jinja --dialect usage is a Warning (not an error) per D-15"

patterns-established:
  - "Pattern: when a generator needs constructor-time params from CLI flags, bypass registry and instantiate directly"

requirements-completed: [CLI-01]

# Metrics
duration: 8min
completed: 2026-04-08
---

# Phase 11 Plan 03: --dialect CLI Flag Summary

**--dialect flag added to generate command, wiring user-selected SQL dialect (default/postgres/spark) directly to SqlJinjaGenerator constructor with allowlist validation and non-sql-jinja warning**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-08T19:44:00Z
- **Completed:** 2026-04-08T19:52:00Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Added `--dialect` Typer option to `generate` command with default value "default"
- Wired dialect through to `SqlJinjaGenerator(dialect=dialect)` by instantiating directly (bypassing registry)
- Implemented allowlist validation against `{"default", "postgres", "spark"}` satisfying threat T-11-05
- Emits `[yellow]Warning[/yellow]` when `--dialect` is used with a non-sql-jinja target (D-15)
- 4 new dialect tests added; all 177 tests pass

## Task Commits

1. **Task 1: RED — Failing tests for --dialect CLI flag** - `0e226b3` (test)
2. **Task 2: GREEN — Add --dialect flag to generate command** - `b6a23a8` (feat)

## Files Created/Modified

- `src/dmjedi/cli/main.py` - Added `--dialect` option, allowlist validation, SqlJinjaGenerator direct instantiation, and non-sql-jinja warning
- `tests/test_cli.py` - Added 4 dialect tests: help output, postgres SQL output, non-sql-jinja warning, invalid dialect rejection

## Decisions Made

- Bypass `registry.get()` for sql-jinja and instantiate `SqlJinjaGenerator(dialect=dialect)` directly — the registry only holds the default-dialect instance and has no mechanism to pass runtime constructor args
- Added explicit `gen: BaseGenerator` annotation to resolve mypy `[assignment]` error from the branched instantiation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed mypy type annotation conflict on gen variable**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Assigning `SqlJinjaGenerator` in the if-branch and `BaseGenerator` in the else-branch caused mypy `[assignment]` error without an explicit type annotation
- **Fix:** Added `gen: BaseGenerator` declaration before the if/else block and a `from dmjedi.generators.base import BaseGenerator` import
- **Files modified:** src/dmjedi/cli/main.py
- **Verification:** `mypy src/dmjedi/cli/` reports no errors for cli/main.py
- **Committed in:** b6a23a8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing type annotation for mypy correctness)
**Impact on plan:** Fix required for strict mypy compliance per CLAUDE.md. No scope creep.

## Issues Encountered

None beyond the mypy annotation issue above.

## Known Stubs

None.

## Threat Flags

None — T-11-05 mitigation (allowlist validation) implemented as specified in the plan's threat model.

## Next Phase Readiness

- `--dialect` is fully wired end-to-end for sql-jinja targets
- CLI-01 requirement fully satisfied
- Ready for remaining phase 11 plans

---
*Phase: 11-output-completeness*
*Completed: 2026-04-08*
