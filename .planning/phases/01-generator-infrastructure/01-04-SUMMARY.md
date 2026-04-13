---
phase: 01-generator-infrastructure
plan: 04
subsystem: testing, infra
tags: [ruff, lint, E501, I001, RUF012, formatting, type-mapping]

# Dependency graph
requires:
  - phase: 01-generator-infrastructure/01-02
    provides: "_TYPE_MAP with duckdb/databricks dialect entries (caused E501 violations)"
  - phase: 01-generator-infrastructure/01-01
    provides: "test_registry.py with unsorted imports and untyped ClassVar"
provides:
  - "Clean ruff lint for types.py (9 E501 resolved)"
  - "Clean ruff lint for test_registry.py (I001 + RUF012 resolved)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-line dict literal format for _TYPE_MAP entries with 5+ dialect keys"

key-files:
  created: []
  modified:
    - src/dmjedi/model/types.py
    - tests/test_registry.py

key-decisions:
  - "No value changes to _TYPE_MAP -- formatting only (whitespace reformatting)"

patterns-established:
  - "Multi-line dict pattern: all _TYPE_MAP entries with 5 dialect keys use one key-value pair per line"

requirements-completed: [GEN-01, GEN-02]

# Metrics
duration: 4min
completed: 2026-04-13
---

# Phase 01 Plan 04: Ruff Lint Gap Closure Summary

**Resolved 11 ruff violations (9 E501 in types.py, 2 in test_registry.py) with zero functional changes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-13T14:41:04Z
- **Completed:** 2026-04-13T14:44:47Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Reformatted all 9 single-line _TYPE_MAP entries with 5 dialect keys to multi-line dict literals, matching the style already used by decimal/timestamp entries
- Fixed import sort order in test_registry.py (spark_declarative before sql_jinja)
- Added ClassVar[list[str]] annotation to DDL_TEMPLATES mutable class attribute
- Full test suite (229 tests) passes unchanged -- zero functional impact

## Task Commits

Each task was committed atomically:

1. **Task 1: Reformat _TYPE_MAP entries in types.py** - `8baf90a` (fix)
2. **Task 2: Fix import order and ClassVar annotation in test_registry.py** - `977ea67` (fix)

## Files Created/Modified
- `src/dmjedi/model/types.py` - Reformatted 9 _TYPE_MAP entries from single-line to multi-line dict literals
- `tests/test_registry.py` - Sorted imports (I001), added ClassVar annotation (RUF012), added typing import

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial worktree state required `git checkout HEAD -- .` to restore files to match HEAD (24a9c99) after `git reset --soft` during branch base correction. This was a worktree setup issue, not a code issue.
- 23 ruff violations remain in other test files (test_cli.py, test_generators.py, test_linter.py, test_model.py, test_parser.py) -- these are pre-existing and out of scope for this plan which targets only types.py and test_registry.py.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The 11 violations targeted by this plan are resolved
- types.py and test_registry.py are fully ruff-clean
- 23 pre-existing violations in other test files remain (out of scope for this gap-closure plan)

## Self-Check: PASSED

- FOUND: src/dmjedi/model/types.py
- FOUND: tests/test_registry.py
- FOUND: 01-04-SUMMARY.md
- FOUND: 8baf90a (Task 1 commit)
- FOUND: 977ea67 (Task 2 commit)

---
*Phase: 01-generator-infrastructure*
*Completed: 2026-04-13*
