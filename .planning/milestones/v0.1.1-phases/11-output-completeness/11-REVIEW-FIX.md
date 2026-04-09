---
phase: 11-output-completeness
fixed_at: 2026-04-08T21:30:00Z
review_path: .planning/phases/11-output-completeness/11-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 11: Code Review Fix Report

**Fixed at:** 2026-04-08T21:30:00Z
**Source review:** .planning/phases/11-output-completeness/11-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-01: IndexError crash when Bridge has empty path in Spark generator

**Files modified:** `src/dmjedi/generators/spark_declarative/generator.py`
**Commit:** 5d1d284
**Applied fix:** Added an early-return guard at the top of `_generate_bridge` — when `bridge.path` is empty, the method now returns a stub comment string (`# Bridge {name}: no path defined\n`) instead of falling through to the unconditional `path[0]` index access that raised `IndexError`.

---

### WR-02: Post-resolve lint errors do not block code generation

**Files modified:** `src/dmjedi/cli/main.py`
**Commit:** 05c4d83
**Applied fix:** After printing model-aware diagnostics, both the `validate` and `generate` commands now count `Severity.ERROR` items among those diagnostics and raise `typer.Exit(code=1)` if any are found. This ensures a broken `effsat-parent-must-be-link` violation blocks generation the same way pre-resolve lint errors do.

---

### WR-03: `lsp` command silently exits 0 without doing anything

**Files modified:** `src/dmjedi/cli/main.py`
**Commit:** 8b9c0f8
**Applied fix:** Replaced the silent `typer.echo` + implicit exit-0 stub with a `Console(stderr=True)` error message (`[red]Error:[/red] LSP server is not yet implemented.`) followed by `raise typer.Exit(code=1)`. The TODO comment was removed as part of the replacement.

---

_Fixed: 2026-04-08T21:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
