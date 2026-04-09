---
phase: 11-output-completeness
reviewed: 2026-04-08T21:10:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - src/dmjedi/cli/main.py
  - src/dmjedi/docs/markdown.py
  - src/dmjedi/generators/spark_declarative/generator.py
  - src/dmjedi/generators/sql_jinja/generator.py
  - src/dmjedi/generators/sql_jinja/templates/effsat.sql.j2
  - src/dmjedi/generators/sql_jinja/templates/samlink.sql.j2
  - tests/test_cli.py
  - tests/test_docs.py
  - tests/test_generators.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-04-08T21:10:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The phase 11 implementation adds EffSat and SamLink output to both generators and the markdown docs layer, with corresponding tests. The core logic is solid and the test coverage is thorough. Three warning-level issues are present: an `IndexError` crash path in `_generate_bridge` when a `Bridge` has an empty path (permitted by the domain model), the `generate` command does not block on post-resolve lint errors (model-aware warnings are printed but do not gate the `generate` command the same way they gate `validate`), and the `lsp` command is a no-op stub that silently succeeds. Three info-level items cover a TODO comment, duplicate post-resolve lint logic, and a missing CLI assertion in the generate-with-dialect warning test.

## Warnings

### WR-01: IndexError crash when Bridge has empty path in Spark generator

**File:** `src/dmjedi/generators/spark_declarative/generator.py:280`

**Issue:** `_generate_bridge` accesses `path[0]` unconditionally at line 280. The `Bridge` model validator (in `model/core.py`) allows `path=[]` — it only rejects paths of length 1 or 2. Passing a `Bridge(path=[])` to `generate()` raises `IndexError: list index out of range` at runtime. The same crash occurs in the SQL Jinja template `bridge.sql.j2` at the `{{ path[0] }}` reference. Both code paths share the same root cause: neither guards against an empty path before indexing.

**Fix:** Add an early return (or skip) when `path` is empty, consistent with how the model validator treats it as "no path defined yet":

```python
def _generate_bridge(self, bridge: Bridge) -> str:
    view_name = f"bridge_{bridge.name}"
    path = bridge.path
    if not path:
        # Empty path is a valid but incomplete bridge; emit a stub comment.
        return f"# Bridge {bridge.name}: no path defined\n"
    path_str = " -> ".join(path)
    ...
```

---

### WR-02: Post-resolve lint errors do not block code generation

**File:** `src/dmjedi/cli/main.py:118-123`

**Issue:** In the `generate` command, after the post-resolve lint pass, `model_aware_diags` are printed but the function does not exit with a non-zero code if any of those diagnostics are `Severity.ERROR`. The `validate` command has the same structure but its intent is to block on errors. As a result a file with a broken `effsat-parent-must-be-link` violation will still emit generated output:

```python
# Current (generate command, lines 118-123)
if model_aware_diags:
    print_diagnostics(model_aware_diags, console)
# <-- no exit here; generation continues regardless of severity
```

The same block in `validate` (lines 59-66) also lacks an explicit exit on ERROR severity among model-aware diagnostics, but at least the validate path is complete before the final "All files valid" message.

**Fix:** Check severity and exit on errors after printing model-aware diagnostics in both commands:

```python
model_aware_error_count = sum(
    1 for d in model_aware_diags if d.severity == Severity.ERROR
)
if model_aware_diags:
    print_diagnostics(model_aware_diags, console)
if model_aware_error_count > 0:
    raise typer.Exit(code=1)
```

---

### WR-03: `lsp` command silently exits 0 without doing anything

**File:** `src/dmjedi/cli/main.py:198-202`

**Issue:** The `lsp` command prints a message and returns without error. Any tooling that invokes `dmjedi lsp` will receive exit code 0, which falsely signals success. If a user or script starts the LSP expecting it to block (as a real language server would), they get an immediate silent exit. A stub command that claims to start a server but immediately terminates is misleading.

**Fix:** Raise `typer.Exit(code=1)` with an explanatory message until the LSP is implemented:

```python
@app.command()
def lsp() -> None:
    """Start the DVML Language Server."""
    console = Console(stderr=True)
    console.print("[red]Error:[/red] LSP server is not yet implemented.")
    raise typer.Exit(code=1)
```

## Info

### IN-01: TODO comment in lsp stub

**File:** `src/dmjedi/cli/main.py:202`

**Issue:** `# TODO: launch pygls server` is a planning comment left in shipping code. This is fine as a reminder but should be tracked in the issue tracker rather than in source.

**Fix:** Remove the inline comment and track the feature as a backlog item.

---

### IN-02: Post-resolve lint block duplicated across three commands

**File:** `src/dmjedi/cli/main.py:55-64, 114-123, 180-188`

**Issue:** The same six-line block (run `lint(module, model=model)`, filter on `effsat-parent-must-be-link`, print diagnostics) is copy-pasted three times into `validate`, `generate`, and `docs`. Any future model-aware lint rule requires the same edit in three places.

**Fix:** Extract a helper:

```python
def _run_post_resolve_lint(
    modules: list[DVMLModule], model: DataVaultModel, console: Console
) -> list[LintDiagnostic]:
    diags = [d for m in modules for d in lint(m, model=model)]
    model_aware = [d for d in diags if d.rule in ("effsat-parent-must-be-link",)]
    if model_aware:
        print_diagnostics(model_aware, console)
    return model_aware
```

---

### IN-03: Warning-check in `test_cli_dialect_non_sql_jinja_warns` uses combined output but Typer runner may not populate `result.stderr`

**File:** `tests/test_cli.py:242`

**Issue:** The test guards `result.stderr` access with `hasattr(result, "stderr") and result.stderr`, but `CliRunner` always populates `result.output` (stdout+stderr mixed by default) when `mix_stderr=True` (the default). The `hasattr` guard is never False — `CliRunner.Result` always has a `.stderr` attribute — so the intent of the fallback is unclear and the `result.stderr` branch may never execute as expected.

**Fix:** Assert directly on `result.output` since the default `CliRunner` mixes streams:

```python
assert "Warning" in result.output or "warning" in result.output.lower()
assert "dialect" in result.output.lower()
```

---

_Reviewed: 2026-04-08T21:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
