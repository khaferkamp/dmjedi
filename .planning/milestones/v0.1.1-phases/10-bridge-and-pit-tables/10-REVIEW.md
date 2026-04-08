---
phase: 10-bridge-and-pit-tables
reviewed: 2026-04-08T20:10:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - pyproject.toml
  - src/dmjedi/generators/spark_declarative/generator.py
  - src/dmjedi/generators/sql_jinja/generator.py
  - src/dmjedi/generators/sql_jinja/templates/bridge.sql.j2
  - src/dmjedi/generators/sql_jinja/templates/pit.sql.j2
  - src/dmjedi/model/core.py
  - src/dmjedi/model/resolver.py
  - tests/fixtures/bridge_pit.dv
  - tests/test_generators.py
  - tests/test_model.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-04-08T20:10:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

This phase adds Bridge and PIT (Point-in-Time) table support to both the Spark Declarative and SQL Jinja generators, along with resolver validation (LINT-04 and LINT-05). The implementation is broadly correct and well-tested. The resolver validations, Jinja templates, and generator logic all work together, and the test suite is thorough.

Four warnings were found: the resolver's PIT satellite validation silently rejects nhsat references, the `Bridge` domain model lacks a minimum-path-length guard analogous to `Link._check_min_refs`, the Spark bridge generator emits raw path strings into `dlt.read()` calls which will break under namespace-qualified names, and the pit SQL template's correlated subquery pattern is fragile when satellite names coincide with SQL reserved words or contain schema-qualified names.

Three info items cover the empty `tracked_satellites` case, variable shadowing in the PIT generator loop output, and a missing `autoescape=True` note for the Jinja environment.

---

## Warnings

### WR-01: Resolver PIT validation ignores nhsat entities — false rejection

**File:** `src/dmjedi/model/resolver.py:374`
**Issue:** The LINT-05 PIT satellite ownership check only looks up `tracked_satellites` references in `model.satellites`. If a user writes a `pit` that tracks an `nhsat` (non-historized satellite), the resolver will raise `"unknown satellite 'X'"` even though the nhsat exists in `model.nhsats`. This is either an undocumented exclusion (nhsats intentionally cannot be tracked in a PIT) or a false positive that breaks valid models. Neither the linter nor resolver documentation clarifies which is intended.

**Fix:** Either explicitly document the exclusion and add a clear error message, or extend the lookup to also check `model.nhsats`:
```python
sat_or_none = (
    model.satellites.get(sat_ref)
    or model.satellites.get(ns_sat_ref)
    or model.nhsats.get(sat_ref)
    or model.nhsats.get(ns_sat_ref)
)
```
If nhsats are intentionally excluded, change the error message to say so:
```python
f"PIT '{pit.qualified_name}' tracks '{sat_ref}' which is not a regular satellite"
f" (nhsats cannot be tracked in a PIT)"
```

---

### WR-02: `Bridge.path` has no minimum-length model validator — direct construction accepts empty path

**File:** `src/dmjedi/model/core.py:121-130`
**Issue:** `Bridge.path` defaults to `[]` and has no `model_validator`. A `Bridge` created directly (not via `resolve()`) with fewer than 3 path elements will silently construct and will cause an `IndexError` in `_generate_bridge` at runtime (when the `range(1, len(path), 2)` loop tries to access `path[i + 1]`). The resolver check at `resolver.py:335-344` only protects models created through `resolve()`. Direct construction in tests and external code has no guard.

**Fix:** Add a `model_validator` mirroring `Link._check_min_refs`:
```python
@model_validator(mode="after")
def _check_min_path(self) -> "Bridge":
    if len(self.path) > 0 and len(self.path) < 3:
        msg = f"Bridge '{self.name}' path must have at least 3 elements (Hub -> Link -> Hub)"
        raise ValueError(msg)
    return self
```
(The `len > 0` guard preserves the ability to construct a default empty-path Bridge for testing the resolver's own short-path check.)

---

### WR-03: Spark bridge generator uses raw path strings in `dlt.read()` — breaks under namespaced paths

**File:** `src/dmjedi/generators/spark_declarative/generator.py:199-202`
**Issue:** `_generate_bridge` emits `dlt.read("{link_name}")` and `dlt.read("{next_hub}")` using raw strings taken directly from `bridge.path`. If a bridge's path contains namespace-qualified names (e.g., `"sales.Customer"`), the generated code will call `dlt.read("sales.Customer")`, which is invalid DLT syntax — DLT table names cannot contain dots. The current fixture and tests only use short unqualified names, so this passes today but is a correctness gap if paths ever include qualified names.

The same issue exists in the SQL template `bridge.sql.j2` at lines 7-17, where `path[i]` is emitted directly into the `FROM` and `JOIN` clauses. A qualified name like `sales.Customer` would generate syntactically valid SQL (catalog-qualified references) but semantically wrong SQL depending on the target system.

**Fix:** Strip the namespace prefix before emitting DLT read names (or document that paths must always use unqualified names). A minimal fix in the generator:
```python
def _table_ref(self, name: str) -> str:
    """Return the unqualified table name for DLT reads."""
    return name.split(".")[-1]
```
Then use `self._table_ref(link_name)` and `self._table_ref(next_hub)` in `_generate_bridge`.

---

### WR-04: PIT SQL template correlated subquery is fragile — same satellite name used as both table ref and subquery alias target

**File:** `src/dmjedi/generators/sql_jinja/templates/pit.sql.j2:13-19`
**Issue:** In the `LEFT JOIN` block, the satellite table is referenced without an alias (`LEFT JOIN {{ sat }}`), then inside the correlated subquery it is re-aliased as `s2` (`FROM {{ sat }} s2`). On the `ON` line, `{{ sat }}.load_ts` references the unaliased outer table. This works in standard SQL, but if `sat` is a schema-qualified name (e.g., `sales.CustomerDetails`), the `ON {{ sat }}.load_ts` reference would require the table to be aliased first. Additionally, if two tracked satellites share the same underlying table (an edge case), the self-join on `load_ts` would produce a Cartesian product.

**Fix:** Add an explicit alias in the generated JOIN to make the pattern unambiguous:
```sql
{%- for sat in pit.tracked_satellites %}
LEFT JOIN {{ sat }} AS {{ sat }}_alias
    ON {{ sat }}_alias.{{ pit.anchor_ref }}_hk = h.{{ pit.anchor_ref }}_hk
    AND {{ sat }}_alias.load_ts = (
        SELECT MAX(s2.load_ts) FROM {{ sat }} s2
        WHERE s2.{{ pit.anchor_ref }}_hk = h.{{ pit.anchor_ref }}_hk
    )
{%- endfor %}
```
And update the SELECT clause accordingly.

---

## Info

### IN-01: PIT with zero tracked satellites is silently valid — semantically meaningless in DV2.1

**File:** `src/dmjedi/model/core.py:133-143`
**Issue:** `Pit.tracked_satellites` defaults to `[]`, and no linter or resolver rule warns when a PIT has no tracked satellites. In Data Vault 2.1, a PIT table with no satellite rows is a non-functional query-assist structure. The test `test_sql_pit_no_create_table` constructs such a model intentionally. While not a crash, it may indicate that users can write semantically empty `pit` declarations without feedback.

**Fix:** Consider adding a lint rule (LINT-06 or similar) or at minimum a resolver warning for empty `tracked_satellites`. Not a resolver error since empty path may be valid during incremental model construction.

---

### IN-02: Variable names `w`, `sat_df`, `sat_latest` are reused for each satellite in generated Spark PIT code

**File:** `src/dmjedi/generators/spark_declarative/generator.py:222-231`
**Issue:** The generated Python code for a multi-satellite PIT reuses the variable names `sat_df`, `w`, and `sat_latest` for each satellite in the loop. Because `df = df.join(sat_latest, ...)` is emitted before the next satellite's variable assignments, the sequential logic is correct. However, if a developer reads or modifies the generated code, the repeated variable names make the logic harder to follow and could cause bugs if the order of statements were ever rearranged.

**Fix:** Suffix the generated variable names with the satellite name:
```python
f'    sat_df_{sat_ref} = dlt.read("{sat_ref}")\n'
f'    w_{sat_ref} = Window.partitionBy("{pit.anchor_ref}_hk")'
...
f'    df = df.join(sat_latest_{sat_ref}, "{pit.anchor_ref}_hk", "left")\n'
```

---

### IN-03: Jinja environment uses `autoescape=False` — note for future template authors

**File:** `src/dmjedi/generators/sql_jinja/generator.py:25-29`
**Issue:** The Jinja2 `Environment` is created with `autoescape=False`. This is correct for SQL generation (autoescaping is for HTML/XML), but future template authors adding user-controlled string interpolation (e.g., table names or column names derived from user input) would need to be aware that there is no automatic escaping. Identifiers containing SQL injection characters (e.g., a column named `a; DROP TABLE`) would be emitted verbatim. The current model's identifiers are validated by the parser/linter before reaching the generator, so this is not an active vulnerability.

**Fix:** Add an inline comment in `generator.py` explaining why `autoescape=False` is safe here and noting the trust boundary:
```python
env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    keep_trailing_newline=True,
    autoescape=False,  # SQL generation: no HTML escaping needed.
    # All template variables are parsed+validated DVML identifiers — safe to emit directly.
)
```

---

_Reviewed: 2026-04-08T20:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
