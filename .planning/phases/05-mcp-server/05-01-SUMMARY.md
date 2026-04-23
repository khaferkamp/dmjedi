---
phase: 05-mcp-server
plan: "01"
subsystem: api
tags: [mcp, pydantic, cli, json, contracts]
requires:
  - phase: 01-generator-infrastructure
    provides: CLI pipeline, generator registry, and dialect routing
provides:
  - Shared `CompileRequest` input normalization for path and inline source modes
  - Stable Pydantic result envelopes for validate, generate, docs, and explain
  - Presentation-free application services that return diagnostics and in-memory artifacts
affects: [05-02, 05-03, cli, mcp]
tech-stack:
  added: [mcp]
  patterns: [shared application service layer, stable machine-readable result contracts]
key-files:
  created:
    [
      src/dmjedi/application/requests.py,
      src/dmjedi/application/results.py,
      src/dmjedi/application/services.py,
      tests/test_cli_json.py,
      tests/test_mcp.py,
    ]
  modified: [pyproject.toml, uv.lock, src/dmjedi/application/__init__.py]
key-decisions:
  - "Inline source mode rejects `import` declarations with a dedicated structured diagnostic instead of attempting filesystem-relative resolution."
  - "Generate and docs services return in-memory artifacts only; disk writes remain an outer CLI concern."
patterns-established:
  - "Application services own discover/parse/lint/resolve/generate/docs/explain orchestration and never print or exit."
  - "CLI JSON and MCP adapters should serialize shared Pydantic result models rather than building ad hoc dict payloads."
requirements-completed: [LLM-01, LLM-02, LLM-03, LLM-04]
duration: 7min
completed: 2026-04-22
---

# Phase 05 Plan 01: MCP Server Foundation Summary

**Shared compile contracts and application services for path-or-inline DVML requests, stable diagnostics, and in-memory generate/docs/explain results**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-22T07:17:48Z
- **Completed:** 2026-04-22T07:24:32Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added a normalized `CompileRequest` model plus stable Pydantic result envelopes for validate, generate, docs, and explain.
- Introduced a presentation-free application service layer that reuses the existing compiler pipeline and converts parse, lint, resolver, and inline-import failures into structured diagnostics.
- Added Wave 0 tests covering schema shape, request normalization, no-disk-write generation, docs artifact shape, and deterministic explain output.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define the shared request/result contracts and Wave 0 test scaffolding** - `feb7d75` (feat)
2. **Task 2: Implement shared validate, generate, docs, and explain services** - `b25ced1` (feat)

## Files Created/Modified

- `pyproject.toml` - Adds the official `mcp>=1.20,<2` runtime dependency
- `src/dmjedi/application/requests.py` - Normalized path-vs-inline compile request model
- `src/dmjedi/application/results.py` - Stable Pydantic result envelopes and artifact/diagnostic shapes
- `src/dmjedi/application/services.py` - Shared orchestration for validate, generate, docs, and explain
- `tests/test_cli_json.py` - Contract tests for schema shape and service-backed artifact behavior
- `tests/test_mcp.py` - Request normalization, inline import rejection, lint mapping, and explain contract tests

## Decisions Made

- Inline source stays self-contained and rejects imports explicitly, matching the threat model and avoiding ambiguous filesystem access.
- Service methods return artifacts in memory and never call write helpers, which keeps JSON and MCP consumers on the same non-side-effecting contract.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Two `git commit` attempts run in parallel hit transient `.git/index.lock` creation races. Retrying the git steps serially resolved the issue without changing task scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 05 now has a canonical application-layer contract for both CLI JSON and MCP adapters.
- Plan `05-02` can wire `--format json` directly to these result models without duplicating compiler logic.
- Plan `05-03` can expose FastMCP tools as thin wrappers around the new services.

## Self-Check

PASSED

---
*Phase: 05-mcp-server*
*Completed: 2026-04-22*
