# Project State

## Current Position
- **Milestone:** 1 — Complete Core CLI
- **Phase:** 6 — Integration Tests & Documentation (complete, plan 2 of 2 complete)
- **Next action:** All phases complete for Milestone 1

## Milestone 1 Progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Wire CLI Commands & Error Reporting | Complete | validate/generate/docs wired, 27 tests pass |
| 2. File Discovery & Import Resolution | In Progress | Plan 2/3: import resolution module done, 39 tests pass |
| 3. Resolver Hardening | Complete | All 3 plans done: validation errors, CLI wiring, 51 tests pass |
| 4. SQL Jinja Generator Polish | Complete | Comma bugs fixed, type mapping added, 61 tests pass |
| 5. Spark Declarative Generator Polish | Complete | Functional DLT code, 65 tests pass |
| 6. Integration Tests & Documentation | Complete | Both plans done: 10 E2E tests, multi-file examples, README updated, 75 tests pass |

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
- SHA-256 hash keys via F.sha2(F.concat_ws("||", ...), 256) for all DLT entity types
- Source convention dlt.read("src_{EntityName}") for DLT pipelines
- Table name prefixes: hub_, sat_, link_ matching DV2.1 convention
- pytest-snapshot for file-based output regression testing
- _sample_model() copied per test file to keep test files independent
- Each example file uses its own namespace (crm, inventory, sales) to demonstrate cross-namespace imports

## Last Updated
2026-04-07 — Phase 6 plan 2 complete: Multi-file examples and README rewrite
