---
phase: 04-lsp-server
plan: "03"
subsystem: lsp
tags: [hover, definition, document-symbols, pygls]
requires:
  - phase: 04-lsp-server
    provides: completion-aware same-document declaration index and cached server analysis
provides:
  - hover details for declarations and references
  - same-document go-to-definition
  - document symbol outline for `.dv` files
affects: [phase-verification, editor-integration]
tech-stack:
  added: []
  patterns: [semantic lookup from cached AST, shared range builders]
key-files:
  created: []
  modified: [src/dmjedi/lsp/analysis.py, src/dmjedi/lsp/protocol.py, src/dmjedi/lsp/server.py, tests/test_lsp.py]
key-decisions:
  - "Semantic navigation remains single-document-only for v0.2.0."
  - "Hover, definition, and symbols all reuse one lookup and range-construction path."
patterns-established:
  - "Cursor lookups first resolve declarations, then same-document references."
  - "Symbol presentation is built from declaration metadata rather than separate AST walkers."
requirements-completed: [LSP-04, LSP-05, LSP-06]
duration: 55min
completed: 2026-04-17
---

# Phase 4: Plan 03 Summary

**The Phase 4 LSP now supports same-document hover, go-to-definition, and document symbols with the full repo test suite still green**

## Accomplishments
- Added symbol lookup helpers that resolve declarations and same-document references from the cached analysis.
- Added protocol builders for hover content, definition locations, and document symbol ranges.
- Wired `hover`, `definition`, and `documentSymbol` handlers and validated them in both focused LSP tests and the repo-wide pytest gate.

## Files Created/Modified
- `src/dmjedi/lsp/analysis.py` - semantic lookup and declaration ordering helpers
- `src/dmjedi/lsp/protocol.py` - hover, definition, and symbol builders
- `src/dmjedi/lsp/server.py` - hover/definition/document symbol handlers
- `tests/test_lsp.py` - semantic LSP coverage and final phase checks

## Verification
- `uv run pytest --no-cov tests/test_lsp.py -x`
- `uv run pytest -x`

## Decisions Made
- Hover content includes entity kind, keys/fields, relationships, and source location using the declaration metadata already present in the AST.
- Document symbols are flat, source-ordered entity entries for v0.2.0 instead of a more complex hierarchy.

## Issues Encountered
- Reference hover lookup initially missed header contexts like `satellite ... of Customer`; the reference-context detector was widened to cover bare prefix forms before the symbol token.

## Next Phase Readiness
- Phase 4 now satisfies the single-document LSP scope and leaves workspace-aware follow-up work cleanly deferred to a later release.
