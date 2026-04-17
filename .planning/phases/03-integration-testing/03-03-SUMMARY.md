---
phase: 03-integration-testing
plan: "03"
subsystem: testing
tags: [duckdb, sqlglot, pytest, snapshots, sql-jinja, databricks, integration-testing]
requires:
  - phase: 03-integration-testing
    plan: "02"
    provides: canonical source rows and DuckDB SQL execution helpers
provides:
  - DuckDB behavioral integration coverage over canonical source rows for hub, satellite, link, bridge, and PIT outputs
  - Full Databricks SQLGlot parse gate across every generated SQL file with file-key failures
  - Refreshed dialect snapshots for DuckDB hash casting and qualified bridge projections
affects:
  - Phase 03 verification gate
  - Future SQL generator changes that touch DuckDB staging hashes or bridge view SQL
tech-stack:
  added: []
  patterns:
    - "Canonical DuckDB integration flow loads src_* tables, creates staging views, inserts into target tables, then asserts downstream query views"
    - "Databricks syntax validation iterates the complete generated file map and reports the failing file key"
key-files:
  created: []
  modified:
    - tests/test_integration.py
    - tests/test_sql_jinja_dialects.py
    - tests/test_hash.py
    - src/dmjedi/generators/sql_jinja/hash.py
    - src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2
    - tests/snapshots/test_sql_jinja_dialects/test_ddl_dialect_snapshot/bridge_CustomerProductBridge-viewsbridge_CustomerProductBridge.sql-duckdb/ddl_bridge_CustomerProductBridge_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_ddl_dialect_snapshot/bridge_CustomerProductBridge-viewsbridge_CustomerProductBridge.sql-databricks/ddl_bridge_CustomerProductBridge_databricks.sql
    - tests/snapshots/test_sql_jinja_dialects/test_ddl_dialect_snapshot/bridge_CustomerProductBridge-viewsbridge_CustomerProductBridge.sql-postgres/ddl_bridge_CustomerProductBridge_postgres.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_hub_Customer-staginghubsCustomer.sql-duckdb/staging_hub_Customer_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_hub_Product-staginghubsProduct.sql-duckdb/staging_hub_Product_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_satellite_CustomerDetails-stagingsatellitesCustomerDetails.sql-duckdb/staging_satellite_CustomerDetails_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_link_CustomerProduct-staginglinksCustomerProduct.sql-duckdb/staging_link_CustomerProduct_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_nhlink_ActiveRelation-staginglinksnhlink_ActiveRelation.sql-duckdb/staging_nhlink_ActiveRelation_duckdb.sql
    - tests/snapshots/test_sql_jinja_dialects/test_staging_dialect_snapshot/staging_samlink_CustomerMatch-staginglinkssamlink_CustomerMatch.sql-duckdb/staging_samlink_CustomerMatch_duckdb.sql
key-decisions:
  - "Kept the DuckDB behavioral flow anchored to explicit generated file keys for Customer, Product, CustomerDetails, CustomerProduct, bridge, and PIT so the test proves representative behavior without redefining generator contracts"
  - "Used SQLGlot parsing over the complete Databricks result.files map and surfaced the failing file key directly in pytest failures"
  - "Folded DuckDB execution-discovered generator fixes into this plan because executable SQL correctness is a Phase 03 requirement, not optional cleanup"
patterns-established:
  - "Behavioral integration tests should use tests/helpers/sql_execution.py and canonical src_* rows instead of hand-built DuckDB schemas"
  - "Generator fixes that change emitted SQL must be reflected in committed snapshots before the dialect module is considered green"
requirements-completed:
  - TEST-01
  - TEST-02
  - TEST-03
duration: 5min
completed: "2026-04-17"
---

# Phase 03 Plan 03: Integration Validation Summary

**Canonical DuckDB source rows now drive executable hub, satellite, link, bridge, and PIT assertions, and every generated Databricks SQL file is syntax-checked through SQLGlot with file-key failures.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-17T06:28:32Z
- **Completed:** 2026-04-17T06:34:02Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Expanded `tests/test_integration.py` from pipeline smoke coverage into a real DuckDB behavioral flow using canonical `src_*` rows and generated SQL outputs.
- Added a full-file Databricks SQLGlot gate in `tests/test_sql_jinja_dialects.py` that parses every generated file and reports the exact failing file key.
- Refreshed affected dialect snapshots after fixing DuckDB hash casting and qualified bridge projections uncovered by real execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend integration tests into full DuckDB behavioral flows** - `b985510` (feat)
2. **Task 2: Add the full Databricks SQLGlot syntax gate to existing dialect tests** - `c47911e` (feat)

TDD RED commits:

1. **Task 1 RED:** `8472bbb` (test)
2. **Task 2 RED:** `198ebca` (test)

## Files Created/Modified
- `tests/test_integration.py` - Adds the canonical DuckDB load, insert, and row-level assertions for raw-vault and query-assist outputs.
- `tests/test_sql_jinja_dialects.py` - Adds the Databricks SQLGlot parse helper and full generated-file parse gate.
- `src/dmjedi/generators/sql_jinja/hash.py` - Casts DuckDB hash inputs to `VARCHAR` before hashing so generated staging SQL executes against typed source tables.
- `src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2` - Qualifies projected bridge columns to avoid ambiguous column references in DuckDB.
- `tests/test_hash.py` and updated dialect snapshots - Lock the generator bug fixes into unit coverage and snapshot baselines.

## Decisions Made
- Used the canonical all-entity fixture but limited behavioral execution to the representative Customer/Product/CustomerDetails/CustomerProduct/bridge/PIT path required by the plan, while still anchoring on real generated file keys.
- Kept the Databricks parse gate inside the existing dialect test module so the Phase 2 snapshot pattern and Phase 3 syntax gate share the same module-scoped generated results.
- Treated DuckDB execution failures in generated SQL as correctness bugs to fix immediately rather than widening test exclusions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed DuckDB staging hash expressions for typed source columns**
- **Found during:** Task 1 (Extend integration tests into full DuckDB behavioral flows)
- **Issue:** Generated DuckDB staging SQL called `sha256` on integer-typed source columns without casting, causing execution failures against real `src_*` tables.
- **Fix:** Updated the DuckDB hash-expression builder to cast each hashed column to `VARCHAR` before `COALESCE` and refreshed the affected unit expectations and snapshots.
- **Files modified:** `src/dmjedi/generators/sql_jinja/hash.py`, `tests/test_hash.py`, DuckDB staging snapshots under `tests/snapshots/test_sql_jinja_dialects/`
- **Verification:** `uv run pytest --no-cov tests/test_integration.py tests/test_hash.py -x`
- **Committed in:** `b985510`

**2. [Rule 1 - Bug] Qualified bridge view projections to avoid ambiguous joins**
- **Found during:** Task 1 (Extend integration tests into full DuckDB behavioral flows)
- **Issue:** Generated bridge views selected bare hash-key column names across joined tables, which DuckDB rejected as ambiguous references.
- **Fix:** Qualified the projected bridge hash-key columns with their source table names and refreshed the bridge snapshots for all dialects.
- **Files modified:** `src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2`, bridge snapshots under `tests/snapshots/test_sql_jinja_dialects/`
- **Verification:** `uv run pytest --no-cov tests/test_integration.py tests/test_sql_jinja_dialects.py -x`
- **Committed in:** `c47911e`

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes were required for executable SQL correctness and directly support the intended Phase 03 validation scope.

## Issues Encountered

- The dialect snapshot module needed snapshot refreshes after the DuckDB execution fixes changed emitted SQL. Running `--snapshot-update` once and then rerunning the clean dialect command resolved that expected churn.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 03 now has executable DuckDB behavioral coverage and a full Databricks syntax gate, so downstream generator work has concrete regression protection.
- Remaining DuckDB incompatibilities in MERGE-based NHLink/EffSat paths were not needed for this plan’s representative behavioral flow and remain outside this plan’s committed scope.

## Self-Check: PASSED

---
*Phase: 03-integration-testing*
*Completed: 2026-04-17*
