---
phase: 10-bridge-and-pit-tables
plan: 01
subsystem: model
tags: [pydantic, resolver, bridge, pit, data-vault, lint]

# Dependency graph
requires:
  - phase: 09-effsat-samlink
    provides: EffSat, SamLink domain model classes, resolver pattern with post-resolution validation
provides:
  - Bridge and Pit domain model classes in model/core.py
  - DataVaultModel bridges and pits dicts
  - Resolver loops for bridge and pit with duplicate detection
  - LINT-04 post-resolution validation (bridge path chain: alternating hub/link, min 3 elements, all refs exist)
  - LINT-05 post-resolution validation (PIT satellite ownership: existence in model.satellites, parent_ref matches anchor)
  - 16 new tests (5 domain model + 11 resolver)
  - tests/fixtures/bridge_pit.dv fixture file
affects: [10-bridge-and-pit-tables/10-02, generators]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD red-green cycle for domain model class + resolver loop additions
    - Post-resolution validation blocks appending to errors list before final raise
    - Qualified name lookup via both bare ref and ns-prefixed ref in post-resolution checks

key-files:
  created:
    - tests/fixtures/bridge_pit.dv
  modified:
    - src/dmjedi/model/core.py
    - src/dmjedi/model/resolver.py
    - tests/test_model.py

key-decisions:
  - "Bridge stores path as flat list[str] (not typed node references) — resolved at validation time"
  - "LINT-04 validation skips further path checks with 'continue' when path too short to avoid index errors"
  - "LINT-05 uses sat_or_none variable name to allow proper mypy narrowing in or-chained dict.get() calls"

patterns-established:
  - "PIT satellite lookup: try bare ref first, then ns-prefixed ref (same pattern as other parent_ref lookups)"
  - "Bridge path validation: even positions must be in model.hubs, odd positions in model.links"

requirements-completed:
  - QUERY-01
  - QUERY-02
  - LINT-04
  - LINT-05

# Metrics
duration: 12min
completed: 2026-04-08
---

# Phase 10 Plan 01: Bridge and PIT Tables Summary

**Bridge and Pit domain model classes with resolver loops, LINT-04 bridge path chain validation, and LINT-05 PIT satellite ownership validation**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-08T17:55:00Z
- **Completed:** 2026-04-08T18:07:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `Bridge` and `Pit` Pydantic v2 classes to `model/core.py` with `qualified_name` property, extending the DataVaultModel with `bridges` and `pits` dicts
- Extended resolver with bridge and pit resolution loops including duplicate detection (same pattern as EffSat/SamLink)
- Implemented LINT-04: bridge path validated for min 3 elements, alternating hub/link pattern, all refs must exist in resolved model
- Implemented LINT-05: PIT satellites validated for existence in model.satellites and parent_ref must match anchor hub
- Added 16 new tests (5 domain model, 11 resolver); full suite grows to 165 tests, all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Bridge and Pit domain model classes + DataVaultModel extension** - `2d85b0a` (feat)
2. **Task 2: Resolver loops + post-resolution validation (LINT-04, LINT-05)** - `453359c` (feat)

_Note: TDD tasks follow RED commit (failing tests) implicit in workflow; both commits represent GREEN phase after implementation._

## Files Created/Modified
- `src/dmjedi/model/core.py` - Added `Bridge` and `Pit` classes before `DataVaultModel`; added `bridges` and `pits` fields to `DataVaultModel`
- `src/dmjedi/model/resolver.py` - Added `Bridge`/`Pit` imports; added bridge and pit resolution loops; added LINT-04 and LINT-05 post-resolution validation blocks
- `tests/test_model.py` - Added 16 new tests across Bridge/Pit domain model and resolver sections
- `tests/fixtures/bridge_pit.dv` - New fixture with complete sales domain: 2 hubs, 1 satellite, 1 link, 1 bridge, 1 pit

## Decisions Made
- Bridge stores `path` as `list[str]` (flat list of entity refs) rather than typed references, matching the BridgeDecl AST shape and enabling clean post-resolution lookup against resolved model
- LINT-04 uses `continue` on too-short paths to avoid out-of-bounds index errors in subsequent per-element checks
- Used `sat_or_none` variable name (rather than `sat`) to satisfy mypy strict mode when using `or`-chained `dict.get()` calls

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mypy type error in LINT-05 sat lookup**
- **Found during:** Task 2 (post-resolution validation)
- **Issue:** `sat = model.satellites.get(sat_ref) or model.satellites.get(ns_sat_ref)` produces type `Satellite | None` but subsequent `elif sat.parent_ref` access requires narrowing; mypy strict mode raised `Incompatible types in assignment`
- **Fix:** Renamed variable to `sat_or_none` and updated the `elif` branch to reference `sat_or_none.parent_ref`
- **Files modified:** src/dmjedi/model/resolver.py
- **Verification:** `mypy src/dmjedi/model/resolver.py` exits 0; all 165 tests pass
- **Committed in:** 453359c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix for mypy strict type narrowing)
**Impact on plan:** Minimal - single variable rename for type correctness. No scope creep.

## Issues Encountered
- mypy strict mode required careful handling of `dict.get() or dict.get()` chains where the result type is `T | None` — the `or`-chain doesn't narrow the type even after `if sat is None:` check in the else branch

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Bridge and Pit domain model + resolver ready for Phase 10 Plan 02 (generator support)
- All LINT-04 and LINT-05 validation in place at resolve time
- 165 tests passing, ruff and mypy clean on modified files

---
*Phase: 10-bridge-and-pit-tables*
*Completed: 2026-04-08*
