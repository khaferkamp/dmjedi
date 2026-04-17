---
phase: 04-lsp-server
plan: "01"
subsystem: lsp
tags: [pygls, lsprotocol, diagnostics, cli]
requires:
  - phase: 03-integration-testing
    provides: stable parser, linter, and repo verification gate
provides:
  - current-document parse and lint analysis for LSP requests
  - diagnostic mapping from parser/linter output to lsprotocol types
  - real `dmjedi lsp` stdio server bootstrap
affects: [04-02, 04-03, editor-integration]
tech-stack:
  added: [pygls, lsprotocol]
  patterns: [single-document analysis cache, thin server handlers]
key-files:
  created: [src/dmjedi/lsp/analysis.py, src/dmjedi/lsp/protocol.py, tests/test_lsp.py]
  modified: [src/dmjedi/lsp/server.py, src/dmjedi/cli/main.py, tests/test_cli.py]
key-decisions:
  - "Kept v0.2.0 analysis current-document-only and avoided workspace indexing."
  - "Mapped parser and linter output through one typed protocol layer before server handlers."
patterns-established:
  - "LSP features read from a per-URI in-memory analysis cache."
  - "Protocol conversions live outside handlers so feature tests can stay transport-free."
requirements-completed: [LSP-01]
duration: 1h
completed: 2026-04-17
---

# Phase 4: Plan 01 Summary

**A real stdio DVML language server now publishes current-document parse and lint diagnostics through `pygls` and starts from `dmjedi lsp`**

## Accomplishments
- Added `DocumentAnalysis` and current-document parser/linter execution for in-memory LSP text.
- Added protocol helpers that map parser and lint findings into LSP diagnostics with reconstructed ranges.
- Replaced the CLI/server stub with a working stdio `pygls` bootstrap and covered it with diagnostics and CLI tests.

## Files Created/Modified
- `src/dmjedi/lsp/analysis.py` - per-document parse/lint analysis model
- `src/dmjedi/lsp/protocol.py` - LSP diagnostic and range mapping helpers
- `src/dmjedi/lsp/server.py` - diagnostics-capable `pygls` server bootstrap
- `src/dmjedi/cli/main.py` - `dmjedi lsp` command now starts the server
- `tests/test_lsp.py` - diagnostics and server-helper coverage
- `tests/test_cli.py` - CLI launch coverage for `dmjedi lsp`

## Verification
- `uv run pytest --no-cov tests/test_lsp.py tests/test_cli.py -k 'lsp or diagnostics' -x`

## Decisions Made
- Current-document analysis only for v0.2.0; no workspace scans or import graph semantics.
- Server handlers stay thin and delegate all parser/linter translation work to reusable helpers.

## Issues Encountered
- Targeted pytest runs initially tripped the global coverage gate; plan verification was rerun with `--no-cov` for narrow checks and then validated again in the full suite.

## Next Phase Readiness
- Completion, hover, definition, and symbol features can build on the same cached analysis object without reparsing architecture changes.
