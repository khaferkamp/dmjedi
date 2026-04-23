---
phase: 01-generator-infrastructure
plan: 02
subsystem: generators
tags: [registry, factory-pattern, type-mapping, duckdb, databricks, cli]

# Dependency graph
requires:
  - phase: 01-generator-infrastructure/01
    provides: "Failing TDD tests for factory pattern and system type mapping"
provides:
  - "Factory-pattern generator registry (classes, not instances)"
  - "System column type entries in _TYPE_MAP (hashkey, load_ts, record_source, hash_diff)"
  - "Dynamic SUPPORTED_DIALECTS derived from _TYPE_MAP keys"
  - "Clean CLI using registry.get(target, dialect=dialect) with no bypass hack"
  - "DuckDB and Databricks dialect keys across all 15 type entries"
affects: [01-generator-infrastructure/03, 02-duckdb-dialect, 03-databricks-dialect]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Factory-pattern registry: stores type[BaseGenerator], instantiates with **params"
    - "Forward-compatible constructors: all generators accept **kwargs"
    - "Dynamic dialect discovery: SUPPORTED_DIALECTS derived from _TYPE_MAP keys"

key-files:
  created:
    - tests/test_registry.py
  modified:
    - src/dmjedi/generators/registry.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - src/dmjedi/generators/sql_jinja/generator.py
    - src/dmjedi/model/types.py
    - src/dmjedi/cli/main.py
    - tests/test_types.py

key-decisions:
  - "Registry stores classes with explicit name strings (cannot call cls.name on uninstantiated class)"
  - "SparkDeclarativeGenerator gets mode='batch' param slot for Phase 6 streaming"
  - "System type default values match existing hardcoded template values for backward compatibility"

patterns-established:
  - "Factory-pattern registry: register(Class, 'name'), get('name', **params) instantiates"
  - "Forward-compat constructors: accept **kwargs to ignore unknown future params"
  - "Dynamic dialect list: add dialect key to _TYPE_MAP, CLI picks it up automatically"

requirements-completed: [GEN-01, GEN-02]

# Metrics
duration: 4min
completed: 2026-04-13
---

# Phase 01 Plan 02: Registry Factory Pattern and System Type Entries Summary

**Factory-pattern registry storing classes with param-passing get(), plus 4 system column type entries with duckdb/databricks dialect support across all 15 _TYPE_MAP entries**

## Performance

- **Duration:** 3m 36s
- **Started:** 2026-04-13T07:45:38Z
- **Completed:** 2026-04-13T07:49:14Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Registry refactored from instance-based to class-based factory pattern; `registry.get("sql-jinja", dialect="postgres")` now works
- Added 4 system column type entries (hashkey, load_ts, record_source, hash_diff) to _TYPE_MAP with all 5 dialect keys
- SUPPORTED_DIALECTS now dynamically derived from _TYPE_MAP keys, automatically includes duckdb and databricks
- CLI bypass hack removed; all generators go through uniform `registry.get(target, dialect=dialect)` path
- All 202 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor registry to factory pattern and update generator constructors** - `11ddb1c` (feat)
2. **Task 2: Add system type entries to _TYPE_MAP and derive SUPPORTED_DIALECTS dynamically** - `17bcedb` (feat)
3. **Task 3: Clean up CLI to use factory pattern and dynamic dialect validation** - `51ce727` (feat)

## Files Created/Modified
- `src/dmjedi/generators/registry.py` - Factory-pattern registry storing type[BaseGenerator] with get(**params) instantiation
- `src/dmjedi/generators/spark_declarative/generator.py` - Added __init__(mode="batch", **kwargs) for forward compat
- `src/dmjedi/generators/sql_jinja/generator.py` - Added **kwargs to __init__ for forward compat
- `src/dmjedi/model/types.py` - Added 4 system type entries, duckdb/databricks keys on all 15 entries, dynamic SUPPORTED_DIALECTS
- `src/dmjedi/cli/main.py` - Dynamic dialect validation via SUPPORTED_DIALECTS, uniform registry.get(target, dialect=dialect)
- `tests/test_registry.py` - New test file with factory pattern and template audit tests
- `tests/test_types.py` - Updated test_supported_dialects to use issubset check

## Decisions Made
- Registry stores classes with explicit name strings passed to register() because `name` is an instance property that cannot be called on the class itself
- SparkDeclarativeGenerator gets `mode="batch"` parameter slot for future Phase 6 streaming support
- System type default values match currently hardcoded template values (BINARY, TIMESTAMP, VARCHAR(255)) to ensure backward compatibility when templates switch to map_type() in Plan 03
- Updated existing test_supported_dialects to use issubset check rather than exact match, allowing forward compatibility as new dialects are added

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created test_registry.py test file**
- **Found during:** Task 1
- **Issue:** Plan 01-01 (Wave 0) creates test_registry.py, but this worktree runs in parallel and the file did not exist
- **Fix:** Created the test file with the same content specified in Plan 01-01 to enable verification
- **Files modified:** tests/test_registry.py
- **Verification:** All 6 TestRegistryFactoryPattern tests pass
- **Committed in:** 11ddb1c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test file creation was necessary because parallel worktree did not have Plan 01-01 output. No scope creep.

## Issues Encountered
- TestTemplateNoHardcodedTypes tests correctly fail (templates still have hardcoded BINARY/TIMESTAMP) -- this is expected RED state from TDD, Plan 03 will make them green

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Registry factory pattern is ready for Plan 03 to use when updating SQL templates to call map_type() for system columns
- SUPPORTED_DIALECTS includes duckdb and databricks, ready for Phase 2 and 3 dialect work
- All generators accept **kwargs, so future params can be passed without breaking changes

## Self-Check: PASSED

All 8 files verified present. All 3 task commits verified (11ddb1c, 17bcedb, 51ce727).

---
*Phase: 01-generator-infrastructure*
*Completed: 2026-04-13*
