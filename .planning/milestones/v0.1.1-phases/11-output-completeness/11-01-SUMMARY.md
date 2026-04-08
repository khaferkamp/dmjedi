---
phase: 11-output-completeness
plan: "01"
subsystem: generators
tags: [jinja2, spark-dlt, effsat, samlink, sql, python, tdd]

requires:
  - phase: 09-effsat-samlink
    provides: EffSat and SamLink domain model classes in model/core.py

provides:
  - effsat.sql.j2 Jinja2 MERGE INTO template for effectivity satellites
  - samlink.sql.j2 Jinja2 MERGE INTO template for same-as links
  - SqlJinjaGenerator loops producing satellites/effsat_{name}.sql files
  - SqlJinjaGenerator loops producing links/samlink_{name}.sql files
  - SparkDeclarativeGenerator._generate_effsat producing satellites/effsat_{name}.py with dlt.apply_changes
  - SparkDeclarativeGenerator._generate_samlink producing links/samlink_{name}.py with dlt.apply_changes

affects:
  - 11-output-completeness (sibling plans)
  - Any future plan that generates pipeline code for EffSat or SamLink entities

tech-stack:
  added: []
  patterns:
    - "EffSat SQL: MERGE ON parent_ref_hk (link hash key, not entity hash key)"
    - "SamLink SQL: MERGE ON samlink_name_hk, two separate FK columns (master_ref_hk, duplicate_ref_hk)"
    - "Spark apply_changes for EffSat/SamLink: no column selection, stored_as_scd_type=1, schema inferred at runtime"

key-files:
  created:
    - src/dmjedi/generators/sql_jinja/templates/effsat.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/samlink.sql.j2
  modified:
    - src/dmjedi/generators/sql_jinja/generator.py
    - src/dmjedi/generators/spark_declarative/generator.py
    - tests/test_generators.py

key-decisions:
  - "EffSat MERGE key is parent_ref_hk (link hash key) matching nhsat pattern — not a separate effsat hash key"
  - "SamLink MERGE key is samlink_name_hk, with master_ref_hk and duplicate_ref_hk as explicit FK columns"
  - "Spark apply_changes for both types omits column selection — dlt infers schema from source at runtime"
  - "EffSat output directory: satellites/ (consistent with nhsat). SamLink output directory: links/ (consistent with nhlink)"

patterns-established:
  - "apply_changes pattern: For current-state entities (EffSat, SamLink, NhSat, NhLink), dlt.apply_changes with stored_as_scd_type=1 and no column listing"
  - "Template naming: effsat.sql.j2 / samlink.sql.j2 mirror nhsat.sql.j2 / nhlink.sql.j2"

requirements-completed: [GEN-01, GEN-02]

duration: 15min
completed: "2026-04-08"
---

# Phase 11 Plan 01: EffSat and SamLink Output Completeness Summary

**SQL Jinja MERGE templates and Spark DLT apply_changes generators for EffSat and SamLink entities, completing pipeline code generation for all DV 2.1 current-state entity types**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-08T21:05:00Z
- **Completed:** 2026-04-08T21:20:00Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 4 (2 created, 2 extended, 1 test file)

## Accomplishments

- Created `effsat.sql.j2` template with `MERGE INTO ... ON parent_ref_hk` pattern mirroring nhsat
- Created `samlink.sql.j2` template with `MERGE INTO ... ON samlink_name_hk` pattern, explicit master/duplicate FK columns
- Extended `SqlJinjaGenerator` with `effsat_tpl` and `samlink_tpl` loops routing to `satellites/` and `links/` directories
- Extended `SparkDeclarativeGenerator` with `_generate_effsat` and `_generate_samlink` producing `dlt.apply_changes(stored_as_scd_type=1)` files
- 6 new TDD tests (SQL valid/no-columns, Spark functional for both types); all 40 generator tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Failing tests for EffSat/SamLink SQL Jinja + Spark generation** - `4b4e820` (test)
2. **Task 2: GREEN — Implement templates, generator loops, and Spark methods** - `4daa4d6` (feat)

_Note: TDD tasks — RED commit (failing tests) then GREEN commit (implementation)_

## Files Created/Modified

- `src/dmjedi/generators/sql_jinja/templates/effsat.sql.j2` - MERGE INTO template for effectivity satellites, ON parent_ref_hk
- `src/dmjedi/generators/sql_jinja/templates/samlink.sql.j2` - MERGE INTO template for same-as links, ON samlink_name_hk with master/duplicate refs
- `src/dmjedi/generators/sql_jinja/generator.py` - Added effsat_tpl and samlink_tpl generation loops
- `src/dmjedi/generators/spark_declarative/generator.py` - Added EffSat/SamLink imports, generation loops, _generate_effsat, _generate_samlink methods
- `tests/test_generators.py` - Added EffSat/SamLink imports, _sample_model_with_effsat_samlink helper, 6 new tests

## Decisions Made

- EffSat MERGE key is `parent_ref_hk` (the link hash key), not a separate EffSat hash key — consistent with nhsat pattern and D-01 specification
- SamLink uses `samlink_name_hk` as the MERGE key per D-04; `master_ref_hk` and `duplicate_ref_hk` are explicit FK columns in the table
- Spark apply_changes for both types omits column listing — `dlt.apply_changes()` infers schema from source at runtime
- Output directory routing: `satellites/effsat_*` for EffSat, `links/samlink_*` for SamLink

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed import line length violating ruff line-length=100 rule**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Single-line import `from dmjedi.model.core import Bridge, DataVaultModel, EffSat, ...` exceeded 100-char limit
- **Fix:** Reformatted to multi-line parenthesized import block; ruff check passes
- **Files modified:** src/dmjedi/generators/spark_declarative/generator.py
- **Verification:** `ruff check src/dmjedi/generators/` returns "All checks passed!"
- **Committed in:** `4daa4d6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - linting bug)
**Impact on plan:** Trivial formatting fix, no scope creep.

## Issues Encountered

None — plan executed as written after lint fix.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- EffSat and SamLink pipeline code generation complete for both SQL Jinja and Spark Declarative targets
- All generator tests pass (40 total)
- Ready for Phase 11 Plan 02 (Bridge/PIT output completeness if planned) or any downstream plan requiring EffSat/SamLink output

---
*Phase: 11-output-completeness*
*Completed: 2026-04-08*
