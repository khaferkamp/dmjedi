---
phase: 10-bridge-and-pit-tables
fixed_at: 2026-04-08T20:30:00Z
review_path: .planning/phases/10-bridge-and-pit-tables/10-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 10: Code Review Fix Report

**Fixed at:** 2026-04-08T20:30:00Z
**Source review:** .planning/phases/10-bridge-and-pit-tables/10-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### WR-01: Resolver PIT validation ignores nhsat entities — false rejection

**Files modified:** `src/dmjedi/model/resolver.py`
**Commits:** fe0a370
**Applied fix:** Extended the LINT-05 satellite lookup at resolver.py:374 to a four-way `or` chain that also checks `model.nhsats.get(sat_ref)` and `model.nhsats.get(ns_sat_ref)` after the existing `model.satellites` lookups. PITs tracking nhsats no longer produce a false "unknown satellite" error.

---

### WR-02: `Bridge.path` has no minimum-length model validator — direct construction accepts empty path

**Files modified:** `src/dmjedi/model/core.py`, `tests/test_model.py`
**Commits:** fbb8bd6, 2b293d4
**Applied fix:** Added `_check_min_path` model_validator (mode="after") to `Bridge` in `core.py`, mirroring `Link._check_min_refs`. The guard condition `0 < len(self.path) < 3` preserves the ability to construct an empty-path Bridge for resolver testing while rejecting paths of length 1 or 2. The validator fires at Pydantic construction time (including inside `resolve()`), so `test_bridge_path_too_short_raises` was updated to expect `ValidationError` instead of `ResolverErrors` — consistent with the `test_link_requires_two_refs` pattern.

---

### WR-03: Spark bridge generator uses raw path strings in `dlt.read()` — breaks under namespaced paths

**Files modified:** `src/dmjedi/generators/spark_declarative/generator.py`
**Commit:** 56bb449
**Applied fix:** Added `_table_ref(self, name: str) -> str` helper method that strips namespace prefixes via `name.split(".")[-1]`. Updated `_generate_bridge` to call `self._table_ref()` on all path elements before interpolating them into `dlt.read()` calls (anchor hub, link, and next hub). Namespace-qualified path names like `sales.Customer` now emit `dlt.read("Customer")` instead of the invalid `dlt.read("sales.Customer")`.

---

### WR-04: PIT SQL template correlated subquery is fragile — same satellite name used as both table ref and subquery alias target

**Files modified:** `src/dmjedi/generators/sql_jinja/templates/pit.sql.j2`
**Commit:** 2aaeabd
**Applied fix:** Added explicit `AS {{ sat }}_alias` alias on `LEFT JOIN {{ sat }}`, and updated all column references in the `ON` clause and `SELECT` list to use `{{ sat }}_alias.column` instead of the bare `{{ sat }}.column`. The correlated subquery inner reference `s2` is unchanged. The pattern is now unambiguous for schema-qualified satellite names. All 78 tests pass after this change.

---

_Fixed: 2026-04-08T20:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
