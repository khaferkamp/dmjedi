---
phase: 3-resolver-hardening
plan: 1
subsystem: model
tags: [resolver, validation, pydantic, data-vault]

# Dependency graph
requires:
  - phase: 2-file-discovery-import-resolution
    provides: multi-module parsing and import resolution
provides:
  - ResolverError/ResolverErrors structured error types
  - Duplicate entity detection (hubs, satellites, links)
  - Satellite parent_ref validation against known hubs/links
affects: [cli-error-wiring, linter-namespace-rules]

# Tech tracking
tech-stack:
  added: []
  patterns: [collect-all-errors-before-raising, qualified-name-dedup, namespace-prefixed-ref-lookup]

key-files:
  created: []
  modified: [src/dmjedi/model/resolver.py]

key-decisions:
  - "Errors collected into list and raised together rather than fail-fast, so users see all issues at once"
  - "Satellite parent_ref checked both bare and namespace-prefixed to handle both qualified and unqualified references"
  - "Duplicate entities skip assignment (first-wins) to avoid cascading errors from overwritten data"

patterns-established:
  - "ResolverError dataclass with source_file/line for structured error reporting"
  - "ResolverErrors exception collecting multiple errors with formatted message"

requirements-completed: [R6.1, R6.2]

# Metrics
duration: 1min
completed: 2026-04-06
---

# Phase 3 Plan 1: Resolver Validation Errors Summary

**Duplicate entity detection and satellite parent_ref validation in resolve() with structured multi-error reporting**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-06T17:43:33Z
- **Completed:** 2026-04-06T17:44:28Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added ResolverError/ResolverErrors types for structured resolver error reporting with source location tracking
- Duplicate detection for hubs, satellites, and links by qualified name (first-wins, skip on duplicate)
- Post-resolution satellite parent_ref validation checking both bare and namespace-prefixed names against hubs and links
- All errors collected before raising so users see every issue at once

## Task Commits

Each task was committed atomically:

1. **Task 1: Resolver validation errors** - `1a82d02` (feat)

## Files Created/Modified
- `src/dmjedi/model/resolver.py` - Added ResolverError/ResolverErrors types, duplicate detection, parent_ref validation

## Decisions Made
- Errors are collected into a list and raised together (not fail-fast) so users see all resolver issues at once
- Satellite parent_ref checked both as bare name and with namespace prefix to handle qualified/unqualified references
- On duplicate, the first entity wins and the duplicate is skipped (not overwritten) to prevent cascading errors

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Resolver validation logic complete, ready for Task 2 (namespace lint rules) and Task 3 (CLI wiring + tests)
- ResolverErrors exception is the public API that CLI commands will catch

---
*Phase: 3-resolver-hardening*
*Completed: 2026-04-06*

## Self-Check: PASSED
