---
phase: 05-mcp-server
plan: 03
subsystem: api
tags: [mcp, fastmcp, typer, pydantic, stdio]
requires:
  - phase: 05-01
    provides: shared application request/result/service contracts for validate, generate, and explain
  - phase: 05-02
    provides: CLI JSON command contracts and machine-readable validation coverage
provides:
  - FastMCP stdio server bootstrap for DMJedi
  - Locked MCP tool surface with validate, generate, and explain only
  - `dmjedi mcp` CLI entrypoint for AI clients
  - MCP contract tests plus repo-wide regression coverage
affects: [cli, ai-workflows, stdio-server]
tech-stack:
  added: []
  patterns: [thin FastMCP adapter, shared service-backed tool wrappers, transport-free CLI command testing]
key-files:
  created: [src/dmjedi/mcp/__init__.py, src/dmjedi/mcp/server.py, src/dmjedi/mcp/tools.py]
  modified: [src/dmjedi/application/services.py, src/dmjedi/cli/main.py, tests/test_mcp.py, tests/test_cli.py]
key-decisions:
  - "The MCP server registers exactly three tools: validate, generate, and explain."
  - "MCP tools normalize source-vs-path inputs into CompileRequest and return shared Pydantic JSON payloads."
  - "Explain entity references are serialized in qualified form to keep the MCP contract machine-resolvable."
patterns-established:
  - "FastMCP bootstrap stays in a singleton server module with registration delegated to tool wrappers."
  - "CLI server entrypoints are tested by monkeypatching imported start helpers instead of launching long-lived transports."
requirements-completed: [LLM-01, LLM-02, LLM-03]
duration: 4min
completed: 2026-04-22
---

# Phase 05 Plan 03: mcp-server Summary

**FastMCP stdio server with locked validate/generate/explain tools and a `dmjedi mcp` CLI entrypoint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-22T07:47:48Z
- **Completed:** 2026-04-22T07:51:15Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added a singleton `FastMCP("dmjedi")` server that runs over stdio and exposes only `validate`, `generate`, and `explain`.
- Implemented thin MCP tool wrappers over the shared application services with structured JSON responses and no disk writes on the MCP path.
- Added `dmjedi mcp` to the Typer CLI and kept the existing `lsp` entrypoint contract stable.
- Verified the new MCP surface with targeted contract tests and a full green repo suite.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the FastMCP server and tool wrappers for validate, generate, and explain**
   `cc6ef69` (test), `9a96a3c` (feat)
2. **Task 2: Add the `dmjedi mcp` entrypoint and run the final phase verification gate**
   `5a42d97` (test), `1d444c3` (feat)

## Files Created/Modified
- `src/dmjedi/mcp/server.py` - FastMCP singleton bootstrap and stdio start helper
- `src/dmjedi/mcp/tools.py` - locked MCP tool wrappers and request normalization
- `src/dmjedi/mcp/__init__.py` - package exports for server and tool entrypoints
- `src/dmjedi/cli/main.py` - new `mcp` command plus preserved `lsp` server seam
- `src/dmjedi/application/services.py` - qualified explain-reference serialization for machine-readable entity links
- `tests/test_mcp.py` - MCP contract coverage for tool list, source/path inputs, virtual artifacts, and explain payloads
- `tests/test_cli.py` - direct CLI command coverage for `dmjedi mcp`

## Decisions Made
- Used direct FastMCP tool registration from a dedicated `register_tools()` helper instead of embedding business logic in decorators.
- Kept MCP output strictly on the shared Pydantic result contracts so CLI JSON and MCP stay aligned.
- Preserved `cli.main.start_server` as the LSP seam to avoid breaking the existing command test while introducing `start_mcp_server`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Qualified explain references in the shared result shape**
- **Found during:** Task 1 (Build the FastMCP server and tool wrappers for validate, generate, and explain)
- **Issue:** `explain` entity references were serialized as local names like `Customer`, which weakened the resolved machine-readable contract.
- **Fix:** Added reference qualification in `src/dmjedi/application/services.py` so explain entities emit namespace-qualified references consistently.
- **Files modified:** `src/dmjedi/application/services.py`
- **Verification:** `uv run pytest --no-cov tests/test_mcp.py -k "tool_list or generate or explain or validate" -x`
- **Committed in:** `9a96a3c`

**2. [Rule 1 - Bug] Restored the existing LSP CLI test seam**
- **Found during:** Task 2 (Add the `dmjedi mcp` entrypoint and run the final phase verification gate)
- **Issue:** Renaming the imported LSP start helper broke `test_lsp_command_starts_server` in the full-suite gate.
- **Fix:** Reintroduced `start_server` as the CLI module alias for the LSP entrypoint while keeping `start_mcp_server` separate for the new MCP command.
- **Files modified:** `src/dmjedi/cli/main.py`
- **Verification:** `uv run pytest`
- **Committed in:** `1d444c3`

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes tightened compatibility and contract correctness without expanding scope.

## Issues Encountered
- The first full-suite run exposed a regression in the existing LSP CLI monkeypatch seam after the MCP import split; fixed inline before the Task 2 commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 05 is ready for closeout and downstream release work: AI clients can now discover `validate`, `generate`, and `explain` through `dmjedi mcp`.
- The MCP surface is covered by both targeted tests and the repo-wide regression suite.

## Self-Check: PASSED

- Found `.planning/phases/05-mcp-server/05-03-SUMMARY.md`
- Found commit `cc6ef69`
- Found commit `9a96a3c`
- Found commit `5a42d97`
- Found commit `1d444c3`

---
*Phase: 05-mcp-server*
*Completed: 2026-04-22*
