---
phase: 4
slug: lsp-server
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-17
updated: 2026-04-23
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x with existing repo test tooling |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_lsp.py tests/test_cli.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5-15 seconds once LSP tests land |

---

## Sampling Rate

- **After every task commit:** run the task’s targeted `uv run pytest ... -x` command
- **After every plan wave:** run the relevant plan-level verification command
- **Before `$gsd-verify-work`:** full suite must be green
- **Max feedback latency:** keep targeted checks under ~10 seconds where feasible

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | LSP-01 | T-04-01 | Parse and lint diagnostics are published from the active document without shelling out through the CLI | unit | `uv run pytest --no-cov tests/test_lsp.py -k diagnostics -x` | ✅ | ✅ green |
| 4-01-02 | 01 | 1 | LSP-01 | T-04-02 | `dmjedi lsp` starts a real server instead of exiting as unimplemented | unit | `uv run pytest --no-cov tests/test_cli.py -k lsp -x` | ✅ | ✅ green |
| 4-02-01 | 02 | 2 | LSP-02, LSP-03 | T-04-03 | Keyword and entity-reference completions stay current-document-only and avoid broad noisy suggestions | unit | `uv run pytest --no-cov tests/test_lsp.py -k completion -x` | ✅ | ✅ green |
| 4-03-01 | 03 | 3 | LSP-04, LSP-05, LSP-06 | T-04-04 | Hover, definition, and document symbols resolve from the active document AST with accurate positions | unit | `uv run pytest --no-cov tests/test_lsp.py -k 'hover or definition or symbols' -x` | ✅ | ✅ green |
| 4-03-02 | 03 | 3 | LSP-01, LSP-02, LSP-03, LSP-04, LSP-05, LSP-06 | T-04-05 | Final repo command proves the LSP server work does not regress existing parser, linter, CLI, or generator behavior | phase-gate | `uv run pytest -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `04-CONTEXT.md` captures the single-document-first v0.2.0 scope
- [x] `04-RESEARCH.md` documents AST-first LSP feature strategy and validation architecture
- [x] `tests/test_lsp.py` created during execution
- [x] `src/dmjedi/lsp/server.py` replaced from placeholder with real server bootstrap

*Wave 0 is complete once the validation-critical scaffolding exists on disk.*

---

## Manual-Only Verifications

*All planned Phase 04 behaviors should be automatable.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or explicit Wave 0 dependencies
- [x] Sampling continuity preserved across the planned LSP feature slices
- [x] Wave 0 covers all known missing validation prerequisites
- [x] No watch-mode flags
- [x] Full-suite gate defined as `uv run pytest`
- [x] `nyquist_compliant: true` set in frontmatter after execution evidence exists

**Approval:** verified 2026-04-23

## Validation Audit 2026-04-23

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 5 |
| Escalated | 0 |

### Evidence

- `uv run pytest --no-cov tests/test_lsp.py -k diagnostics -x` → `3 passed`
- `uv run pytest --no-cov tests/test_cli.py -k lsp -x` → `1 passed`
- `uv run pytest --no-cov tests/test_lsp.py -k completion -x` → `6 passed`
- `uv run pytest --no-cov tests/test_lsp.py -k 'hover or definition or symbols' -x` → `4 passed`
- `uv run pytest -x` → `363 passed`, `92.83%` coverage
