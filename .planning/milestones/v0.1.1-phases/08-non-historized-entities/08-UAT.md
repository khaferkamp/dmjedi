---
status: complete
phase: 08-non-historized-entities
source: [08-01-SUMMARY.md, 08-02-SUMMARY.md]
started: 2026-04-08T16:00:00Z
updated: 2026-04-08T16:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Parse nhsat declaration
expected: A `.dv` file with `nhsat` keyword parses successfully. Run `dmjedi validate examples/sales-domain.dv` (or a test file with nhsat) — no parse errors.
result: pass

### 2. Parse nhlink declaration
expected: A `.dv` file with `nhlink` keyword and 2+ hub references parses successfully. No parse errors.
result: pass

### 3. Resolve nhsat into model
expected: Run `pytest tests/test_model.py::test_resolve_nhsat -v` — test passes, confirming nhsat resolves with correct parent_ref and columns.
result: pass

### 4. Resolve nhlink into model
expected: Run `pytest tests/test_model.py::test_resolve_nhlink -v` — test passes, confirming nhlink resolves with correct hub_references.
result: pass

### 5. NhSat invalid parent rejected
expected: Run `pytest tests/test_model.py::test_nhsat_invalid_parent_raises -v` — test passes, confirming resolver raises error for nhsat referencing non-existent parent.
result: pass

### 6. SQL Jinja generates MERGE for nhsat
expected: Run `pytest tests/test_generators.py::test_sql_nhsat_output_valid -v` — test passes, confirming generated SQL contains `MERGE INTO` and does NOT contain `INSERT INTO` or `hash_diff`.
result: pass

### 7. SQL Jinja generates MERGE for nhlink
expected: Run `pytest tests/test_generators.py::test_sql_nhlink_output_valid -v` — test passes, confirming generated SQL contains `MERGE INTO` with hub reference hash keys.
result: pass

### 8. Spark DLT generates apply_changes for nhsat
expected: Run `pytest tests/test_generators.py::test_spark_nhsat_output_functional -v` — test passes, confirming generated Python contains `dlt.apply_changes` and `stored_as_scd_type=1`.
result: pass

### 9. Spark DLT generates apply_changes for nhlink
expected: Run `pytest tests/test_generators.py::test_spark_nhlink_output_functional -v` — test passes, confirming generated Python contains `dlt.apply_changes` and `stored_as_scd_type=1`.
result: pass

### 10. Full test suite green
expected: Run `pytest` — all 128 tests pass, no regressions from Phase 7.
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
