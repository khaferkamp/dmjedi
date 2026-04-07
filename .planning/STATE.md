# Project State

## Current Position
- **Milestone:** 1 — Complete Core CLI
- **Phase:** 4 — SQL Jinja Generator Polish (complete, plan 1 of 1 complete)
- **Next action:** `/gsd-execute-phase 5` to start Spark Declarative Generator Polish

## Milestone 1 Progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Wire CLI Commands & Error Reporting | Complete | validate/generate/docs wired, 27 tests pass |
| 2. File Discovery & Import Resolution | In Progress | Plan 2/3: import resolution module done, 39 tests pass |
| 3. Resolver Hardening | Complete | All 3 plans done: validation errors, CLI wiring, 51 tests pass |
| 4. SQL Jinja Generator Polish | Complete | Comma bugs fixed, type mapping added, 61 tests pass |
| 5. Spark Declarative Generator Polish | Pending | |
| 6. Integration Tests & Documentation | Pending | |

## Key Decisions
- Small phases (1-3 tasks) for tight feedback loops
- Both Spark and SQL generators are equally important
- Team audience — needs to be reliable and well-documented
- No hard deadline
- Console(stderr=True) for all Rich CLI diagnostic output
- Extracted _parse_all helper to DRY file parsing across generate and docs commands
- B008 ruff per-file ignore for standard Typer argument defaults
- Visited set updated after recursion (not before) for correct cycle detection in imports
- Resolver errors collected into list and raised together (not fail-fast) so users see all issues at once
- Resolver errors displayed with same red E prefix as lint errors for consistent CLI output
- map_type registered as Jinja2 global (not filter) for cleaner template syntax
- Dialect passed via constructor to preserve BaseGenerator ABC interface

## Last Updated
2026-04-07 — Phase 4 plan 1 complete: SQL template comma fixes and type mapping
