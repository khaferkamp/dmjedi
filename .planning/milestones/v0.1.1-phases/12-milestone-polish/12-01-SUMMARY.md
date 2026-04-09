---
phase: 12-milestone-polish
plan: 01
subsystem: linter, cli
tags: [linter, naming-convention, LINT-03, bridge, pit, docs, error-gate, TDD]

requires:
  - phase: 09-effsat-samlink
    provides: effsat-parent-must-be-link linter rule and LINT-03 naming convention implementation
  - phase: 10-bridge-pit
    provides: BridgeDecl, PitDecl AST nodes and DVMLModule.bridges / DVMLModule.pits fields
provides:
  - _check_naming() covers all 9 DV 2.1 entity types (hub, sat, link, nhsat, nhlink, effsat, samlink, bridge, pit)
  - dmjedi docs exits code 1 on model-aware ERROR diagnostics, matching validate/generate behavior
  - effsat-parent-must-be-link severity corrected to ERROR (semantic fix)
affects: [linter tests, CLI error handling, LINT-03 completeness]

tech-stack:
  added: []
  patterns:
    - All three data-producing CLI commands (validate, generate, docs) now consistently gate on model_aware_error_count > 0

key-files:
  created: []
  modified:
    - src/dmjedi/lang/linter.py
    - src/dmjedi/cli/main.py
    - tests/test_linter.py
    - tests/test_cli.py

key-decisions:
  - "Changed effsat-parent-must-be-link severity from WARNING to ERROR: an effsat on a hub is semantically invalid in DV 2.1, ERROR is correct"
  - "Kept model_aware_error_count guard pattern identical to validate/generate for CLI consistency"

patterns-established:
  - "Naming check pattern: append (entity_type, module.entity_list) tuples to checks list in _check_naming()"
  - "Model-aware error gate: sum ERROR-severity diags, raise typer.Exit(code=1) before any output generation"

requirements-completed:
  - LINT-03

duration: 15min
completed: 2026-04-08
---

# Phase 12 Plan 01: Milestone Polish Summary

**LINT-03 bridge/pit naming coverage added to all 9 entity types and docs command model-aware error gate added matching validate/generate behavior**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-08T19:39:00Z
- **Completed:** 2026-04-08T19:54:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `_check_naming()` now covers all 9 DV 2.1 entity types; bridge and pit naming-prefix violations now produce `naming-convention` warnings
- `dmjedi docs` exits code 1 when model-aware lint finds ERROR-level diagnostics, consistent with `validate` and `generate`
- Corrected `effsat-parent-must-be-link` severity from WARNING to ERROR (an effectivity satellite must be on a link, not a hub — this is a structural violation, not a style issue)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend _check_naming() to cover bridge and pit (LINT-03)** - `5e7c222` (feat)
2. **Task 2: Add model-aware error gate to docs command** - `99cad48` (feat)

## Files Created/Modified
- `src/dmjedi/lang/linter.py` - Added `("bridge", module.bridges)` and `("pit", module.pits)` to checks list; changed effsat-parent-must-be-link severity to ERROR
- `src/dmjedi/cli/main.py` - Added `model_aware_error_count` guard to `docs()` before `generate_markdown` call
- `tests/test_linter.py` - Added `test_naming_all_nine_types`, `test_naming_bridge_missing_prefix`, `test_naming_pit_missing_prefix`, `test_naming_bridge_correct_prefix`, `test_naming_pit_correct_prefix`; updated effsat severity assertion to ERROR; removed unused pytest import; added BridgeDecl/PitDecl imports
- `tests/test_cli.py` - Added `test_docs_exits_on_model_aware_error` and `test_docs_passes_on_warnings_only`

## Decisions Made
- Changed `effsat-parent-must-be-link` severity from WARNING to ERROR. The plan test required this to produce an exit-code-1, and ERROR is the semantically correct severity (effsat on a hub is a DV 2.1 structural violation, not a style issue).
- Used identical 3-line pattern (`sum(...) / if > 0 / raise Exit`) as existing validate/generate guards.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected effsat-parent-must-be-link severity from WARNING to ERROR**
- **Found during:** Task 2 (docs error gate)
- **Issue:** Plan test `test_docs_exits_on_model_aware_error` required effsat-on-hub to produce exit code 1. The `model_aware_error_count` guard only counts ERROR-severity diagnostics. The rule was emitting WARNING, so no exit code 1 would ever trigger.
- **Fix:** Changed `severity=Severity.WARNING` to `severity=Severity.ERROR` in `_check_naming` for `effsat-parent-must-be-link`; updated existing test assertion from `Severity.WARNING` to `Severity.ERROR`.
- **Files modified:** `src/dmjedi/lang/linter.py`, `tests/test_linter.py`
- **Verification:** All 202 tests pass; docs test exits code 1 for effsat-on-hub
- **Committed in:** `99cad48` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Necessary correctness fix. An effectivity satellite attached to a hub is semantically invalid in DV 2.1; ERROR is appropriate. No scope creep.

## Issues Encountered
None beyond the severity bug described in deviations.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- LINT-03 requirement fully satisfied: all 9 entity types covered
- CLI error handling consistent across all three data-producing commands
- v0.1.1 milestone polish complete; project ready for `/gsd-new-milestone`

---
*Phase: 12-milestone-polish*
*Completed: 2026-04-08*
