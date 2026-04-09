---
phase: 08-non-historized-entities
reviewed: 2026-04-08T15:30:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/dmjedi/generators/spark_declarative/generator.py
  - src/dmjedi/generators/sql_jinja/generator.py
  - src/dmjedi/generators/sql_jinja/templates/nhlink.sql.j2
  - src/dmjedi/generators/sql_jinja/templates/nhsat.sql.j2
  - src/dmjedi/model/core.py
  - src/dmjedi/model/resolver.py
  - tests/test_generators.py
  - tests/test_model.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-04-08T15:30:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

This phase adds `NhSat` and `NhLink` entity types (non-historized satellites and links) across the model layer, resolver, and both generators. The implementation is structurally sound and follows the existing patterns for `Satellite` and `Link` well. The new Jinja2 templates produce correct MERGE semantics, and the Spark DLT generator correctly uses `apply_changes` with `stored_as_scd_type=1`.

Three warnings require attention: the resolver's NhSat parent-ref validation has a gap (it does not accept `nhlinks` as valid parents, silently rejecting a structurally valid attachment), the `NhLink` constructor in the resolver can raise an unhandled Pydantic `ValidationError` instead of a `ResolverError`, and the Spark DLT nhsat function name collides with the table name in a way that may cause a DLT pipeline registration error at runtime.

---

## Warnings

### WR-01: NhSat parent-ref validation does not accept NhLinks as valid parents

**File:** `src/dmjedi/model/resolver.py:178-194`

**Issue:** The post-resolution validation block for `NhSat` parent refs checks `model.hubs` and `model.links`, but not `model.nhlinks`. An `NhSat` attached to an `NhLink` (e.g., `nhsat Status of SomeNhLink { ... }`) will always fail validation with "unknown parent" even though `NhLink` is a structurally valid parent for a non-historized satellite. The equivalent check for regular `Satellite` (lines 159-175) has the same scope, but that may be intentional for Satellite. For NhSat the restriction is not documented anywhere and `NhLink` is a natural attachment target in DV2.1.

**Fix:**
```python
# resolver.py ~line 180 — add nhlinks check
for nhsat in model.nhsats.values():
    ref = nhsat.parent_ref
    ns_ref = f"{nhsat.namespace}.{ref}" if nhsat.namespace else ref
    if (
        ref not in model.hubs
        and ref not in model.links
        and ref not in model.nhlinks          # <-- add this
        and ns_ref not in model.hubs
        and ns_ref not in model.links
        and ns_ref not in model.nhlinks       # <-- add this
    ):
        errors.append(
            ResolverError(
                message=(
                    f"NhSat '{nhsat.qualified_name}'"
                    f" references unknown parent '{ref}'"
                ),
            )
        )
```

If attaching NhSat to NhLink is intentionally out of scope for this phase, add a comment explaining the restriction so it is not treated as a bug later.

---

### WR-02: NhLink construction in resolver raises unhandled Pydantic ValidationError

**File:** `src/dmjedi/model/resolver.py:134-156`

**Issue:** `NhLink(...)` is constructed at line 135 with `hub_references=nhlink_decl.references`. If the linter did not catch a declaration with fewer than 2 references (or if the resolver is called directly without linting), Pydantic's `model_validator` raises a `ValidationError`. This exception is not caught and will propagate out of `resolve()` as a raw `ValidationError` instead of the expected `ResolverErrors`. Callers that catch only `ResolverErrors` will see an unhandled exception. The same issue exists for `Link` at line 87 (pre-existing), but the NhLink block should not perpetuate it.

**Fix:**
```python
# Wrap NhLink construction to convert Pydantic validation failures into ResolverErrors
from pydantic import ValidationError as PydanticValidationError

for nhlink_decl in module.nhlinks:
    try:
        nhlink = NhLink(
            name=nhlink_decl.name,
            namespace=ns,
            hub_references=nhlink_decl.references,
            columns=[
                Column(name=f.name, data_type=f.data_type) for f in nhlink_decl.fields
            ],
        )
    except PydanticValidationError as exc:
        errors.append(
            ResolverError(
                message=str(exc),
                source_file=module.source_file,
                line=nhlink_decl.loc.line,
            )
        )
        continue
    qname = nhlink.qualified_name
    ...
```

The same fix should be applied to the `Link` construction block at line 87 (pre-existing gap).

---

### WR-03: DLT function name `{table_name}_target` conflicts with the table name `{table_name}` in nhsat output

**File:** `src/dmjedi/generators/spark_declarative/generator.py:136-146`

**Issue:** The `@dlt.table(name="{table_name}")` decorator at line 133 registers a DLT table named `nhsat_{nhsat.name}`. The Python function is named `{table_name}_target` (i.e., `nhsat_{nhsat.name}_target`). Databricks DLT associates the dataset name from the decorator's `name=` argument, not the function name, so the registration itself is correct. However, `apply_changes(target="{table_name}", ...)` at line 141 uses the decorator's table name. The DLT runtime requires that the `@dlt.table`-decorated function exist as a schema-declaration stub before `apply_changes` references it. The function name (`_target` suffix) does not match the table name, which is legal in DLT — but the `_generate_nhlink` method (lines 149-171) uses the same `_target` suffix pattern for consistency. Verify with the Databricks DLT docs that a `pass`-body `@dlt.table` function is accepted as a schema stub when `apply_changes` is used in the same pipeline file; if it is not, both `_generate_nhsat` and `_generate_nhlink` will produce pipelines that fail at runtime with no test catching it (tests only assert string content, not DLT validity).

**Fix:** Add a comment in the template string and a corresponding test note that explicitly documents the DLT schema-stub requirement, or replace the `pass` body with a `return spark.range(0)` / schema-inference approach that is known to work, citing the DLT documentation version used to confirm the pattern.

---

## Info

### IN-01: `NhLink` default `hub_references=[]` combined with model_validator gives a confusing error for omitted argument

**File:** `src/dmjedi/model/core.py:79`

**Issue:** `hub_references: list[str] = []` makes the field optional at the Python level, but the `model_validator` at line 82 immediately rejects any instance with fewer than 2 entries. Calling `NhLink(name="x")` raises a `ValidationError` about "at least 2 hubs" with no indication that `hub_references` was not provided. This mirrors the same pattern in `Link` (pre-existing) but is worth flagging in the new code. The default `[]` is misleading — there is no valid empty-references NhLink.

**Fix:** Either remove the default and make the field required (`hub_references: list[str]`), or keep the default and update the validator error message to say "hub_references must contain at least 2 entries; got 0 (field may have been omitted)". Removing the default is cleaner.

---

### IN-02: Test `test_spark_nhsat_no_columns` does not assert `apply_changes` structure completeness

**File:** `tests/test_generators.py:428-442`

**Issue:** The test for an `NhSat` with no columns (lines 428-442) only checks that `"apply_changes"` and `"stored_as_scd_type=1"` appear in the output. It does not assert that `keys=` and `sequence_by=` are present, which are required fields for `apply_changes`. The equivalent positive test `test_spark_nhsat_output_functional` (line 397) does check `Customer_hk` in the output, but the no-columns variant skips this. If the generator regresses and emits a broken `apply_changes` call for empty-column entities, this test would not catch it.

**Fix:**
```python
def test_spark_nhsat_no_columns():
    ...
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code
    assert 'keys=["Parent_hk"]' in code      # <-- add
    assert 'sequence_by=F.col("load_ts")' in code  # <-- add
```

---

_Reviewed: 2026-04-08T15:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
