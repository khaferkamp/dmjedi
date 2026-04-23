---
phase: 02-sql-dialects
plan: "02"
subsystem: generators
tags: [sql, jinja2, staging-views, hash, duckdb, databricks, postgres, data-vault]

requires:
  - phase: 02-sql-dialects
    plan: "01"
    provides: hash_expr Jinja2 global, q filter, dialect global, build_hash_expr function

provides:
  - 7 staging view Jinja2 templates (hub, satellite, link, nhsat, nhlink, effsat, samlink)
  - SqlJinjaGenerator produces staging/ companion files alongside DDL for all 7 physical entity types
  - Hub staging: dialect-aware hash from business keys, stg_ prefix, src_ source table
  - Satellite staging: parent_hk passthrough, hash_diff computed from columns
  - Link staging: composite hash from hub reference hash key column names
  - NhSat/EffSat staging: parent_hk passthrough, no hash_diff (non-historized)
  - NhLink staging: composite hash from hub ref hk names
  - SamLink staging: hash from master_ref and duplicate_ref hash key column names
  - Bridge and PIT: no staging views (query-assist views excluded by design)

affects:
  - 02-03-PLAN: dialect-specific tests will cover staging view output per dialect
  - CLI generate command: now produces 16 files for sales-domain.dv (8 DDL + 8 staging)

tech-stack:
  added: []
  patterns:
    - "Staging views always generated alongside DDL (per D-06, not opt-in)"
    - "Jinja2 set+append pattern for building hub_ref hash key name lists in link/nhlink templates"
    - "Inline Jinja2 list literal [a ~ '_hk', b ~ '_hk'] for samlink two-ref hash"
    - "map(attribute='name') | list for extracting column name lists from model objects"

key-files:
  created:
    - src/dmjedi/generators/sql_jinja/templates/staging_hub.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_satellite.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_link.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_nhsat.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_nhlink.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_effsat.sql.j2
    - src/dmjedi/generators/sql_jinja/templates/staging_samlink.sql.j2
  modified:
    - src/dmjedi/generators/sql_jinja/generator.py
    - tests/test_integration.py

key-decisions:
  - "Staging views are always generated (not opt-in) per D-06 — no flag or config needed"
  - "Link and NhLink templates use set+append Jinja2 pattern to build hub ref hk name list, avoiding Python list comprehension syntax which is not valid in Jinja2"
  - "SamLink uses inline Jinja2 list literal [master_ref ~ '_hk', dup_ref ~ '_hk'] which is valid in Jinja2 (confirmed)"
  - "Staging files placed in staging/{entity_type}/{name}.sql paths (staging/hubs/, staging/satellites/, staging/links/) parallel to DDL directories"
  - "Integration test split: 8 DDL files checked for CREATE TABLE, 8 staging files checked for CREATE OR REPLACE VIEW"

requirements-completed:
  - DIAL-01
  - DIAL-02
  - DIAL-03
  - DIAL-04

duration: ~20min
completed: "2026-04-15"
---

# Phase 02 Plan 02: Staging View Templates Summary

**7 staging view Jinja2 templates created and wired into SqlJinjaGenerator, producing dialect-aware SHA-256 hash key computation for all physical Data Vault 2.1 entity types alongside their DDL files.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-04-15T11:36:00Z
- **Completed:** 2026-04-15T11:41:46Z
- **Tasks:** 2
- **Files modified:** 9 (7 created, 2 modified)

## Accomplishments

- Created 7 staging view templates, each using the `hash_expr` Jinja2 global (from Plan 01) for dialect-aware SHA-256 hash computation
- Hub staging views compute `{hub.name}_hk` from all business key columns using `hash_expr(hub.business_keys | map(attribute='name') | list)`
- Satellite staging views pass through the parent `{parent_ref}_hk` and compute `hash_diff` from all satellite columns
- Link staging views compute composite hash from hub reference hash key column names (`{ref}_hk` for each hub reference)
- NhSat and EffSat staging views provide parent_hk passthrough without hash_diff (non-historized pattern)
- NhLink staging views compute composite hash from hub ref hk names (same pattern as link)
- SamLink staging views hash from master_ref and duplicate_ref hash key column names
- Bridge and PIT entities intentionally excluded (query-assist views, no source data loading)
- Updated `SqlJinjaGenerator.generate()` to render staging companions alongside DDL for all 7 physical entity types
- Updated `test_e2e_sql_pipeline` to assert 8 DDL files separately from 8 staging files
- CLI now produces 16 files for sales-domain.dv via `dmjedi generate --target sql-jinja`
- All 218 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 7 staging view templates** - `f712b97` (feat)
2. **Task 2: Wire staging views into generator and update integration tests** - `d242a0e` (feat)

## Files Created/Modified

- `src/dmjedi/generators/sql_jinja/templates/staging_hub.sql.j2` - New: hub staging with hash from business keys
- `src/dmjedi/generators/sql_jinja/templates/staging_satellite.sql.j2` - New: satellite staging with hash_diff
- `src/dmjedi/generators/sql_jinja/templates/staging_link.sql.j2` - New: link staging with composite hash from hub ref hks
- `src/dmjedi/generators/sql_jinja/templates/staging_nhsat.sql.j2` - New: non-historized satellite staging
- `src/dmjedi/generators/sql_jinja/templates/staging_nhlink.sql.j2` - New: non-historized link staging
- `src/dmjedi/generators/sql_jinja/templates/staging_effsat.sql.j2` - New: effectivity satellite staging
- `src/dmjedi/generators/sql_jinja/templates/staging_samlink.sql.j2` - New: same-as link staging with master/dup hash
- `src/dmjedi/generators/sql_jinja/generator.py` - Added staging template rendering for all 7 entity types
- `tests/test_integration.py` - Updated `test_e2e_sql_pipeline` to split DDL/staging file assertions

## Decisions Made

- Staging views always generated (not opt-in): Per D-06, every DDL entity automatically produces a companion staging view. No `--with-staging` flag needed.
- Jinja2 set+append pattern for link/nhlink hash key list: Jinja2 does not support Python list comprehensions; the `{% set ref_hk_names = [] %}{% for ref ... %}{% set _ = ref_hk_names.append(...) %}` pattern is the correct Jinja2 idiom for building lists from loops.
- SamLink inline list literal: `[samlink.master_ref ~ '_hk', samlink.duplicate_ref ~ '_hk']` is valid Jinja2 syntax for two-element list construction (confirmed working).
- Staging file paths mirror DDL structure: `staging/hubs/`, `staging/satellites/`, `staging/links/` parallel the DDL `hubs/`, `satellites/`, `links/` paths.

## Deviations from Plan

None — plan executed exactly as written. All templates match the plan specification. Jinja2 inline list literal `[a ~ '_hk', b ~ '_hk']` worked as expected for samlink (plan noted it should be tested, confirmed working).

## Known Stubs

None — all staging views render live model data. Hash expressions are computed from actual business key and column names from the parsed DVML model. Source table names (`src_{entity}`) are conventional placeholder names per T-02-07 (accepted, design-intentional).

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes. Staging views operate on local DVML model data. Threat surface covered by plan's T-02-05, T-02-06, T-02-07 (all accepted).

## Self-Check: PASSED

All 7 template files verified on disk. Both task commits verified in git log (f712b97, d242a0e). All 218 tests pass.

---

*Phase: 02-sql-dialects*
*Completed: 2026-04-15*
