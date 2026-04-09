---
phase: 09-effectivity-satellites-and-same-as-links
reviewed: 2026-04-08T16:25:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - src/dmjedi/cli/main.py
  - src/dmjedi/lang/linter.py
  - src/dmjedi/model/core.py
  - src/dmjedi/model/resolver.py
  - tests/fixtures/effsat_samlink.dv
  - tests/test_linter.py
  - tests/test_model.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-04-08T16:25:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

This phase adds EffSat (effectivity satellite) and SamLink (same-as link) support across the domain model, resolver, linter, and CLI. The implementation follows established patterns from existing entity types (Hub, Satellite, Link, NhSat, NhLink). The domain model and resolver are well-structured with proper duplicate detection and parent-ref validation for EffSat. However, SamLink ref validation is incomplete in the resolver, and the CLI has a code duplication issue with post-resolve lint logic that also silently discards model-aware warnings without affecting the exit code.

## Warnings

### WR-01: SamLink references not validated against resolved model

**File:** `src/dmjedi/model/resolver.py:230-290`
**Issue:** The resolver performs post-resolution validation for satellite parent refs (line 231), nhsat parent refs (line 250), and effsat parent refs (line 269), but does not validate that SamLink `master_ref` or `duplicate_ref` actually resolve to known hubs in the model. A SamLink referencing a non-existent hub will silently pass resolver validation, unlike every other entity type with parent refs.
**Fix:** Add a post-resolution validation block for SamLink refs after line 285:
```python
# Post-resolution validation: samlink hub refs
for samlink in model.samlinks.values():
    for ref_name, ref_label in [
        (samlink.master_ref, "master"),
        (samlink.duplicate_ref, "duplicate"),
    ]:
        ns_ref = f"{samlink.namespace}.{ref_name}" if samlink.namespace else ref_name
        if ref_name not in model.hubs and ns_ref not in model.hubs:
            errors.append(
                ResolverError(
                    message=(
                        f"SamLink '{samlink.qualified_name}'"
                        f" {ref_label} references unknown hub '{ref_name}'"
                    ),
                )
            )
```

### WR-02: Post-resolve model-aware lint warnings not counted toward exit code

**File:** `src/dmjedi/cli/main.py:55-66`
**Issue:** In the `validate` command (and similarly in `generate` at lines 99-107 and `docs` at lines 150-158), model-aware diagnostics from post-resolve linting are printed but never counted. The exit code decision at line 43 only checks `all_diagnostics` (pre-resolve), and the final "All files valid" message at line 65-66 checks both lists but only for emptiness (not severity). If a model-aware rule is later elevated from WARNING to ERROR, it would be printed but not cause a non-zero exit code.
**Fix:** After printing model-aware diagnostics, count errors and exit if any are found:
```python
model_aware_errors = sum(1 for d in model_aware_diags if d.severity == Severity.ERROR)
if model_aware_errors > 0:
    raise typer.Exit(code=1)
```

### WR-03: SamLink same-hub lint check uses naive string comparison

**File:** `src/dmjedi/lang/linter.py:137`
**Issue:** The `_check_samlinks` function compares `samlink.master_ref != samlink.duplicate_ref` using direct string equality. This works correctly when both refs use the same form (both unqualified), but would produce a false positive if one ref were qualified (`ns.Customer`) and the other unqualified (`Customer`). While the current grammar likely produces consistent ref forms, this is fragile if cross-namespace refs are supported in the future.
**Fix:** Consider normalizing refs before comparison, or document the assumption that refs within a single module are always in the same form. For now, this is a minor concern given the current grammar constraints.

## Info

### IN-01: Post-resolve lint logic duplicated across three CLI commands

**File:** `src/dmjedi/cli/main.py:55-66`
**Issue:** The post-resolve lint block (lint with model, filter by rule name, print) is copy-pasted identically in `validate` (lines 55-66), `generate` (lines 99-107), and `docs` (lines 150-158). The hardcoded rule filter tuple `("effsat-parent-must-be-link",)` must be updated in three places when new model-aware rules are added.
**Fix:** Extract a helper function:
```python
def _post_resolve_lint(
    modules: list[DVMLModule], model: DataVaultModel, console: Console
) -> list[LintDiagnostic]:
    """Run model-aware lint rules and print diagnostics."""
    MODEL_AWARE_RULES = {"effsat-parent-must-be-link"}
    diags: list[LintDiagnostic] = []
    for module in modules:
        diags.extend(d for d in lint(module, model=model) if d.rule in MODEL_AWARE_RULES)
    if diags:
        print_diagnostics(diags, console)
    return diags
```

### IN-02: TODO comment in LSP stub

**File:** `src/dmjedi/cli/main.py:172`
**Issue:** `# TODO: launch pygls server` -- pre-existing stub, not part of this phase.
**Fix:** No action needed for this phase; the TODO is a known placeholder per CLAUDE.md.

---

_Reviewed: 2026-04-08T16:25:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
