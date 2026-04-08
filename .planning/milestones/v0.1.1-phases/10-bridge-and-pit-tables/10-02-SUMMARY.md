---
phase: 10-bridge-and-pit-tables
plan: "02"
subsystem: generators
tags: [tdd, sql-jinja, spark-declarative, bridge, pit, views]
dependency_graph:
  requires: ["10-01"]
  provides: ["bridge-sql-view", "pit-sql-view", "bridge-spark-view", "pit-spark-view"]
  affects: ["generators/sql_jinja/generator.py", "generators/spark_declarative/generator.py"]
tech_stack:
  added: []
  patterns:
    - "Jinja2 template with range() iteration over path list for JOIN chain"
    - "@dlt.view decorated function (not @dlt.table) for query-assist views"
    - "Window.partitionBy().orderBy() + row_number() for latest-record PIT logic"
key_files:
  created:
    - src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/pit.sql.j2
  modified:
    - src/dmjedi/generators/sql_jinja/generator.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - tests/test_generators.py
    - pyproject.toml
decisions:
  - "Bridge and PIT output files go to views/ directory (not tables/, satellites/, or links/)"
  - "SQL Jinja uses CREATE OR REPLACE VIEW (not CREATE TABLE) for both entity types"
  - "Spark DLT uses @dlt.view (not @dlt.table) for both entity types"
  - "PIT Spark uses Window + row_number() over anchor_ref_hk for latest-record selection"
  - "Added pythonpath = [\"src\"] to worktree pyproject.toml for worktree-isolated pytest execution"
metrics:
  duration_seconds: 201
  completed_date: "2026-04-08"
  tasks_completed: 2
  files_changed: 6
---

# Phase 10 Plan 02: Bridge and PIT Generator Extensions Summary

SQL Jinja and Spark DLT generators extended with CREATE OR REPLACE VIEW and @dlt.view output for bridge (JOIN chain) and PIT (Window-based left join snapshot) entities, output to views/ directory.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | SQL Jinja bridge/PIT templates + generator | c39a4d3 | bridge.sql.j2, pit.sql.j2, sql_jinja/generator.py, pyproject.toml |
| 2 | Spark DLT bridge/PIT view generation | 3f8abae | spark_declarative/generator.py, tests/test_generators.py |

## What Was Built

- `bridge.sql.j2`: Jinja2 template generating `CREATE OR REPLACE VIEW bridge_{name} AS SELECT ... FROM ... JOIN ...` with a loop over the path list (alternating hub/link entries)
- `pit.sql.j2`: Jinja2 template generating `CREATE OR REPLACE VIEW pit_{name} AS SELECT ... FROM anchor LEFT JOIN satellite WHERE load_ts = (SELECT MAX ...)` for each tracked satellite
- SQL Jinja `generate()` extended with `bridge_tpl` and `pit_tpl` blocks, output files in `views/` directory
- Spark DLT generator imports `Bridge, Pit`; adds `_IMPORTS_VIEW` constant with `from pyspark.sql.window import Window`; `_generate_bridge()` produces `@dlt.view` function with dlt.read + .join() chain; `_generate_pit()` produces `@dlt.view` function with Window/row_number latest-record logic and `"left"` join
- 8 new tests in `tests/test_generators.py` covering SQL and Spark bridge/PIT correctness

## Verification

```
pytest tests/test_generators.py -k "bridge or pit" -x -v  # 8 passed
pytest -x                                                   # 173 passed
ruff check src/dmjedi/generators/                          # All checks passed
mypy src/dmjedi/generators/                                # Success: no issues found
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added pythonpath to pyproject.toml for worktree isolation**
- **Found during:** Task 1 GREEN phase
- **Issue:** The worktree uses the main project's `.venv` which has dmjedi installed in editable mode from the main project's `src/` directory, not the worktree's `src/`. Tests ran against the unmodified main project files.
- **Fix:** Added `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in the worktree's `pyproject.toml`. pytest now prepends the worktree's `src/` to `sys.path`, taking precedence over the editable install.
- **Files modified:** pyproject.toml
- **Commit:** c39a4d3

## Known Stubs

None. All bridge and PIT generator output produces functional SQL or PySpark code with no placeholders, hardcoded empty values, or TODO markers.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: path-traversal (mitigated) | sql_jinja/generator.py | Bridge/PIT files use hard-coded "views/" prefix + entity.name — no user-controlled path components. Consistent with T-10-05 mitigation already in place. |

## Self-Check: PASSED

- src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2: FOUND
- src/dmjedi/generators/sql_jinja/templates/pit.sql.j2: FOUND
- src/dmjedi/generators/sql_jinja/generator.py contains bridge_tpl: VERIFIED
- src/dmjedi/generators/spark_declarative/generator.py contains _generate_bridge: VERIFIED
- Commit c39a4d3: FOUND
- Commit 3f8abae: FOUND
- All 173 tests: PASSED
