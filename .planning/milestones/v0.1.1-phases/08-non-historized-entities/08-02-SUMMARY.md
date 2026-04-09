---
phase: 08-non-historized-entities
plan: "02"
subsystem: generators
tags: [generators, sql-jinja, spark-dlt, nhsat, nhlink, merge, apply_changes]
dependency_graph:
  requires: [08-01]
  provides: [nhsat-sql-generation, nhlink-sql-generation, nhsat-spark-generation, nhlink-spark-generation]
  affects: [sql-jinja-generator, spark-declarative-generator]
tech_stack:
  added: []
  patterns: [MERGE INTO (SQL), dlt.apply_changes with stored_as_scd_type=1 (Spark)]
key_files:
  created:
    - src/dmjedi/generators/sql_jinja/templates/nhsat.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/nhlink.sql.j2
  modified:
    - src/dmjedi/generators/sql_jinja/generator.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - tests/test_generators.py
decisions:
  - "nhsat SQL uses parent_ref_hk as MERGE ON key; nhlink SQL uses link_name_hk"
  - "Spark DLT uses apply_changes with stored_as_scd_type=1; no column enumeration (runtime inference)"
  - "nhsat/nhlink files use nhsat_/nhlink_ prefix to distinguish from historized sat_/link_ files"
metrics:
  duration_minutes: 20
  completed_date: "2026-04-08"
  tasks_completed: 2
  files_changed: 5
---

# Phase 08 Plan 02: Non-Historized Entity Generators Summary

**One-liner:** MERGE INTO SQL Jinja templates and dlt.apply_changes() Spark DLT methods for NhSat and NhLink, with 7 new tests covering trailing-comma edge cases and column-omission semantics.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | SQL Jinja MERGE templates and generator wiring | b6629b1 | nhsat.sql.j2, nhlink.sql.j2, sql_jinja/generator.py |
| 2 | Spark DLT _generate_nhsat and _generate_nhlink | 1c2798c | spark_declarative/generator.py |
| TDD RED | Failing tests for both tasks | 488beb6 | tests/test_generators.py |

## What Was Built

### Task 1: SQL Jinja Templates

Two new Jinja2 templates generating MERGE INTO SQL for non-historized entities:

- `nhsat.sql.j2`: MERGE using `parent_ref_hk` as the ON-clause match key. Handles zero-column case without trailing comma. Excludes `hash_diff` and `load_end_ts` (historized-only fields).
- `nhlink.sql.j2`: MERGE using `link_name_hk` as ON-clause key. Handles zero-column and hub-references-only cases cleanly.

Both templates use the same comma-safety pattern as existing `link.sql.j2` (Jinja `loop.last` + `columns` conditional).

`SqlJinjaGenerator.generate()` extended: nhsat files land at `satellites/nhsat_X.sql`, nhlink files at `links/nhlink_X.sql`.

### Task 2: Spark DLT Generator

`SparkDeclarativeGenerator` extended with two new private methods:

- `_generate_nhsat(nhsat: NhSat)`: Produces `@dlt.table` stub + `dlt.apply_changes(stored_as_scd_type=1)` using `parent_ref_hk` as the key. No column enumeration — `apply_changes()` infers full schema from source dataset at runtime.
- `_generate_nhlink(nhlink: NhLink)`: Same pattern using `link_name_hk` as the key.

Both methods follow the design decision documented in the plan: user-defined columns are validated at the model layer (resolver) but intentionally do not appear in generated DLT Python code. Tests explicitly assert column names are absent from Spark output.

## Test Results

- **Before this plan:** 121 tests passing
- **After this plan:** 128 tests passing (+7 new generator tests)

New tests:
1. `test_sql_nhsat_output_valid` — MERGE INTO, Customer_hk, no historized fields
2. `test_sql_nhlink_output_valid` — MERGE INTO, AB_hk, A_hk, B_hk, amount
3. `test_sql_nhsat_no_columns_valid` — trailing-comma edge case
4. `test_sql_nhlink_no_columns_valid` — trailing-comma edge case
5. `test_spark_nhsat_output_functional` — apply_changes, stored_as_scd_type=1, no column names in output
6. `test_spark_nhlink_output_functional` — apply_changes, stored_as_scd_type=1, no column names in output
7. `test_spark_nhsat_no_columns` — empty columns still generates valid apply_changes code

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All generator methods are fully implemented and tested.

## Threat Flags

None. No new network endpoints, auth paths, or trust-boundary changes introduced. Generated code is inert text output per T-08-05 and T-08-06 in the threat register.

## Self-Check: PASSED

Files created/exist:
- src/dmjedi/generators/sql_jinja/templates/nhsat.sql.j2: FOUND
- src/dmjedi/generators/sql_jinja/templates/nhlink.sql.j2: FOUND
- tests/test_generators.py (modified): FOUND

Commits exist:
- 488beb6 (TDD RED tests): FOUND
- b6629b1 (Task 1 feat): FOUND
- 1c2798c (Task 2 feat): FOUND

Full suite: 128 passed, 0 failed.
Ruff: all checks passed.
Mypy: no issues found in 8 source files.
