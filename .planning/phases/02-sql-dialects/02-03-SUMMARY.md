---
phase: 02-sql-dialects
plan: "03"
subsystem: tests
tags: [sql, jinja2, snapshot-testing, hash, duckdb, databricks, postgres, data-vault, dial-01, dial-02, dial-03, dial-04, dial-05]

requires:
  - phase: 02-sql-dialects
    plan: "01"
    provides: hash.py module, q filter, CHAR(64) type, registry **kwargs instantiation
  - phase: 02-sql-dialects
    plan: "02"
    provides: 7 staging view templates, SqlJinjaGenerator staging output

provides:
  - Comprehensive all-entity-types DVML fixture (all 9 DV2.1 entity types in one file)
  - 21 unit tests for build_hash_expr (all 3 dialects, default, edge cases, D-02 hash_algo)
  - 4 unit tests for q filter / double-quote identifier pattern
  - 30 DDL snapshot tests (10 entities x 3 dialects)
  - 24 staging view snapshot tests (8 entities x 3 dialects)
  - Structural validation tests: quoting, CHAR(64), hash functions, COALESCE/delimiter, ANSI header
  - 54 committed snapshot files covering all entity/dialect combinations

affects:
  - Phase 02 quality gate: all DIAL-01 through DIAL-05 requirements validated end-to-end

tech-stack:
  added: []
  patterns:
    - "pytest-snapshot --snapshot-update for initial generation, then exact match on subsequent runs"
    - "scope=module fixtures for shared parsed model and generated results across parametrized tests"
    - "HASH_MARKERS dict for dialect -> expected function name mapping in structural tests"

key-files:
  created:
    - tests/fixtures/all_entity_types.dv
    - tests/test_hash.py
    - tests/test_sql_jinja_dialects.py
    - tests/snapshots/test_sql_jinja_dialects/ (54 snapshot files)
  modified: []

key-decisions:
  - "scope=module used on all_entity_model and generated_results fixtures to parse/generate once for all 74 parametrized tests, avoiding repeated I/O"
  - "Snapshot tests use distinct names (ddl_{entity}_{dialect}.sql, {entity}_{dialect}.sql) to be self-documenting and avoid collisions"
  - "B007 lint fix: unused loop variable entity renamed to _entity in structural validation loops"

requirements-completed:
  - DIAL-01
  - DIAL-02
  - DIAL-03
  - DIAL-04
  - DIAL-05

duration: ~8min
completed: "2026-04-15"
---

# Phase 02 Plan 03: Dialect Snapshot Tests Summary

**313-test suite with 95 new tests: 21 hash unit tests, 74 parameterized dialect snapshot tests across all 9 DV2.1 entity types for DuckDB, Databricks SQL, and PostgreSQL — validating DIAL-01 through DIAL-05 end-to-end.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-15T11:41:00Z
- **Completed:** 2026-04-15T11:49:38Z
- **Tasks:** 2
- **Files created:** 57 (fixture + 2 test files + 54 snapshot files)

## Accomplishments

- Created `tests/fixtures/all_entity_types.dv` covering all 9 DV2.1 entity types: hub, satellite, link, nhsat, nhlink, effsat, samlink, bridge, pit — verified parses and resolves without errors
- Created `tests/test_hash.py` with 21 unit tests: DuckDB sha256(), Databricks sha2(,256), PostgreSQL encode/sha256/bytea, default SHA256(), multi-column delimiter (|| '||' ||), COALESCE NULL handling, D-02 hash_algo override (explicit, unknown fallback, registry factory wiring), and q filter double-quote pattern
- Created `tests/test_sql_jinja_dialects.py` with 74 parametrized tests:
  - 30 DDL snapshot tests (10 entities x 3 dialects)
  - 24 staging view snapshot tests (8 entities x 3 dialects)
  - 3x test_all_ddl_files_present, 3x test_all_staging_files_present
  - 3x test_ddl_identifiers_quoted, 3x test_ddl_uses_char64_for_hash_keys
  - test_databricks_ansi_header, test_non_databricks_no_ansi_header
  - 3x test_staging_hub_uses_correct_hash_function, 3x test_staging_uses_coalesce_and_delimiter
- Generated and committed 54 snapshot files (30 DDL + 24 staging) in `tests/snapshots/test_sql_jinja_dialects/`
- Full test suite: 313 tests pass (218 pre-existing + 95 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hash expression and quoting unit tests** - `ed3c13f` (test)
2. **Task 2: Create all-entity-types fixture and parameterized dialect snapshot tests** - `aa4d280` (feat)

## Files Created

- `tests/fixtures/all_entity_types.dv` - Comprehensive fixture with all 9 DV2.1 entity types
- `tests/test_hash.py` - 21 unit tests: build_hash_expr (3 dialects + default), edge cases, D-02 hash_algo override, q filter
- `tests/test_sql_jinja_dialects.py` - 74 parametrized snapshot + structural validation tests
- `tests/snapshots/test_sql_jinja_dialects/test_ddl_dialect_snapshot/` - 30 DDL snapshots
- `tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/` - 24 staging view snapshots

## Decisions Made

- `scope="module"` on `all_entity_model` and `generated_results` fixtures: The fixture file is parsed once and SQL generated once per dialect per test session. This avoids repeating I/O across 74 parametrized tests that all share the same model.
- Snapshot file naming convention `ddl_{entity}_{dialect}.sql` and `{entity}_{dialect}.sql`: makes snapshots self-documenting in the filesystem and avoids name collisions between DDL and staging tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] B007 lint error: unused loop variable `entity` in structural validation loops**
- **Found during:** Task 2 (ruff lint check)
- **Issue:** The `test_all_ddl_files_present` and `test_all_staging_files_present` functions iterate `for entity, file_key in ...items()` but only use `file_key`. Ruff B007 flags unused loop control variables.
- **Fix:** Renamed `entity` to `_entity` in both loops per ruff convention.
- **Files modified:** tests/test_sql_jinja_dialects.py
- **Committed in:** aa4d280 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 lint fix)
**Impact on plan:** Trivial variable rename. No behavior change.

## Known Stubs

None — all tests use live generated SQL output from the real generator. Snapshot files capture actual generator output, not placeholder content.

## Threat Flags

None — test files and fixture introduce no new network endpoints, auth paths, file access patterns, or schema changes. Threat surface covered by plan's T-02-08 and T-02-09 (both accepted).

## Self-Check: PASSED

All created files verified on disk. Both task commits verified in git log (ed3c13f, aa4d280). 313 tests pass. 54 snapshot files committed.

---

*Phase: 02-sql-dialects*
*Completed: 2026-04-15*
