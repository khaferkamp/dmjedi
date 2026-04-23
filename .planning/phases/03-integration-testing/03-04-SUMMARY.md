# Plan 03-04 Summary

## Outcome

Closed the remaining Phase 03 DuckDB execution gap. The non-historized SQL templates now execute against staging views instead of raw `src_*` tables, SAMLink output now disambiguates same-ref master/duplicate columns, and integration coverage executes the full generated DuckDB file map with row assertions for NHSat, NHLink, EffSat, and SAMLink.

## Files Changed

- `src/dmjedi/generators/sql_jinja/templates/nhsat.sql.j2`
- `src/dmjedi/generators/sql_jinja/templates/nhlink.sql.j2`
- `src/dmjedi/generators/sql_jinja/templates/effsat.sql.j2`
- `src/dmjedi/generators/sql_jinja/templates/samlink.sql.j2`
- `src/dmjedi/generators/sql_jinja/templates/staging_samlink.sql.j2`
- `tests/test_integration.py`
- `tests/test_generators.py`
- `tests/snapshots/test_sql_jinja_dialects/...` (affected NHSat/NHLink/EffSat/SAMLink snapshots)

## Task Results

### Task 1

- Removed qualified target columns from the four MERGE `UPDATE SET` clauses.
- Redirected NHSat, NHLink, EffSat, and SAMLink MERGE statements to `stg_*` views so required derived columns (`load_ts`, `record_source`, hash keys) are available at execution time.
- Added same-ref SAMLink column disambiguation (`master_*` / `duplicate_*`) to keep generated SQL valid when `master_ref == duplicate_ref`.

### Task 2

- Added a DuckDB integration test that executes the complete generated file map for the canonical all-entity fixture.
- Expanded behavioral assertions to cover:
  - `CurrentStatus`
  - `ActiveRelation`
  - `RelationValidity`
  - `CustomerMatch`
- Reused the existing canonical fixture and source-row payloads without changing generator interfaces or output paths.

## Verification

- `uv run pytest --no-cov tests/test_integration.py -k duckdb -x`
- `uv run pytest --no-cov tests/test_generators.py -k 'effsat or samlink' -x`
- `uv run pytest --no-cov tests/test_sql_jinja_dialects.py -k 'nhsat or nhlink or effsat or samlink' -x`
- `uv run pytest -x`

## Deviations

- The original gap plan assumed the parser qualifier fix was sufficient. Direct execution exposed two additional runtime blockers:
  - MERGE templates were reading `src_*` tables instead of staging views.
  - SAMLink output became invalid when master and duplicate references resolved to the same hub key name.
- Both were fixed as part of this gap closure because they blocked the stated Phase 03 truth: full generated DuckDB SQL must execute successfully.
