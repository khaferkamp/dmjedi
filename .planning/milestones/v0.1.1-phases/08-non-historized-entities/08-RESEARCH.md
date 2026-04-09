# Phase 8: Non-Historized Entities - Research

**Researched:** 2026-04-08
**Domain:** Data Vault 2.1 domain model extension, resolver, Spark DLT generator, SQL Jinja generator
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** NhSat and NhLink get their own separate classes in `model/core.py`, not subclasses of Satellite/Link. Follows pre-roadmap decision for separate types and keeps generator dispatch clean.
- **D-02:** DataVaultModel gets `nhsats: dict[str, NhSat]` and `nhlinks: dict[str, NhLink]` as new fields. Generators iterate separate dicts — no type-checking or flag-filtering needed.
- **D-03:** SQL output for nhsat/nhlink uses `MERGE INTO` pattern. Template: `MERGE INTO target USING source ON key WHEN MATCHED THEN UPDATE SET ... WHEN NOT MATCHED THEN INSERT (...)`.
- **D-04:** Spark DLT output uses `dlt.apply_changes()` with `stored_as_scd_type=1`. Declarative, fits existing DLT generator pattern.
- **D-05:** MERGE match key is the parent hash key — nhsat matches on `parent_hk`, nhlink matches on its own `link_hk` computed from hub references. Mirrors historized versions.
- **D-06:** nhsat parent_ref validation follows same rules as regular satellite — parent must be an existing hub or link. Same validation logic, same error messages.
- **D-07:** NhLink enforces same minimum 2-hub reference rule as Link, using the same Pydantic `model_validator` pattern.
- **D-08:** nhsat files go in `satellites/` directory (filename: `nhsat_X.py` or `nhsat_X.sql`). nhlink files go in `links/` directory (filename: `nhlink_X.py` or `nhlink_X.sql`). Same dirs as historized, prefix distinguishes them.
- **D-09:** SQL Jinja uses separate template files: `nhsat.sql.j2` and `nhlink.sql.j2`. MERGE pattern is fundamentally different from INSERT. Follows Phase 7 decision D-11.

### Claude's Discretion

- Exact `apply_changes()` parameter configuration (sequence_by, track_history, etc.)
- SQL MERGE template variations across dialects (default, postgres, spark)
- Test fixture `.dv` file design for nhsat/nhlink examples
- Whether NhSat/NhLink domain classes share a base mixin for common fields or duplicate them

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENTITY-03 | User can declare `nhsat` with `of` referencing a hub or link (current-state-only satellite) | AST node NhSatDecl already exists; domain model class NhSat needs adding to core.py; resolver loop for nhsats needed; generator methods `_generate_nhsat()` needed in both generators |
| ENTITY-04 | User can declare `nhlink` with `references` to 2+ hubs (current-state-only link) | AST node NhLinkDecl already exists; domain model class NhLink needs adding to core.py with 2-hub validator; resolver loop for nhlinks needed; generator methods `_generate_nhlink()` needed in both generators |
| GEN-03 | Non-historized entities generate MERGE/overwrite patterns (not INSERT) | SQL uses MERGE INTO via new templates; Spark uses dlt.apply_changes() with scd_type=1 |
</phase_requirements>

---

## Summary

Phase 8 extends the pipeline at three layers — domain model, resolver, and both generators — to support non-historized satellites (`nhsat`) and non-historized links (`nhlink`). The parser layer is already complete from Phase 7: grammar rules, AST nodes (`NhSatDecl`, `NhLinkDecl`), transformer methods, and `DVMLModule.nhsats`/`nhlinks` lists all exist and are tested.

The work is a clean replication of the existing Satellite/Link patterns with two differences: (1) domain model classes are separate types (not subclasses), and (2) generators emit MERGE/overwrite semantics instead of INSERT. Every integration point follows an already-established pattern in the codebase — there are no novel architectural decisions required.

The full test suite of 111 tests passes on the current codebase (`uv run pytest`, 1.62s). Tests for this phase should follow the functional assertion style in `test_generators.py` and the inline-source style in `test_model.py`.

**Primary recommendation:** Implement in four sequential steps: (1) add NhSat/NhLink to `model/core.py`, (2) extend `model/resolver.py`, (3) add nhsat/nhlink SQL Jinja templates and wire into SqlJinjaGenerator, (4) add `_generate_nhsat()`/`_generate_nhlink()` methods to SparkDeclarativeGenerator.

---

## Standard Stack

### Core (already in project)
| Component | Version/Location | Purpose |
|-----------|-----------------|---------|
| Pydantic v2 BaseModel | project dependency | Domain model classes — use `model_validator(mode="after")` for NhLink 2-hub check |
| Lark Earley parser | project dependency | Grammar already handles nhsat/nhlink — no changes needed |
| Jinja2 | project dependency | Template engine for SQL Jinja generator — add two new `.sql.j2` files |
| `dlt.apply_changes()` | Databricks DLT API | Spark SCD Type 1 / overwrite semantics for nhsat/nhlink |

[VERIFIED: codebase grep — pyproject.toml not read, but all imports confirmed working in 111 passing tests]

### No New Dependencies
This phase requires zero new package installs. All needed libraries are already project dependencies.

---

## Architecture Patterns

### Existing Patterns to Replicate Exactly

**Pattern 1: Domain model class shape** (from `model/core.py`)

Every resolved entity follows this structure:
```python
# Source: src/dmjedi/model/core.py — Satellite class
class NhSat(BaseModel):
    name: str
    namespace: str = ""
    parent_ref: str
    columns: list[Column] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

NhLink replicates Link's shape and adds the `model_validator`:
```python
# Source: src/dmjedi/model/core.py — Link class (exact pattern to copy)
class NhLink(BaseModel):
    name: str
    namespace: str = ""
    hub_references: list[str] = []
    columns: list[Column] = []

    @model_validator(mode="after")
    def _check_min_refs(self) -> "NhLink":
        if len(self.hub_references) < 2:
            msg = f"NhLink '{self.name}' must reference at least 2 hubs"
            raise ValueError(msg)
        return self

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

**Pattern 2: DataVaultModel extension** (from `model/core.py`)

Add two fields to `DataVaultModel`:
```python
# After existing links field:
nhsats: dict[str, NhSat] = {}
nhlinks: dict[str, NhLink] = {}
```

**Pattern 3: Resolver loop** (from `model/resolver.py`)

The nhsat resolver loop mirrors the satellite loop exactly. The nhlink resolver loop mirrors the link loop exactly. Key: post-resolution parent_ref validation for nhsats must also check `model.nhlinks` (nhsat can parent off a link).

Resolver also needs to import NhSat, NhLink from core, and validate nhsat parent refs against hubs AND links AND nhlinks.

```python
# Source: src/dmjedi/model/resolver.py — satellite resolution pattern (exact copy + rename)
for nhsat_decl in module.nhsats:
    nhsat = NhSat(
        name=nhsat_decl.name,
        namespace=ns,
        parent_ref=nhsat_decl.parent_ref,
        columns=[Column(name=f.name, data_type=f.data_type) for f in nhsat_decl.fields],
    )
    qname = nhsat.qualified_name
    if qname in model.nhsats:
        errors.append(ResolverError(
            message=f"Duplicate nhsat '{qname}' redefined in {module.source_file or '<string>'}:{nhsat_decl.loc.line}",
            source_file=module.source_file,
            line=nhsat_decl.loc.line,
        ))
    else:
        model.nhsats[qname] = nhsat
```

Post-resolution nhsat parent validation (same logic as satellite validation, but checks nhlinks too — D-06 says parent can be a hub or link):
```python
# Extend existing satellite parent-ref validation block, or add new block after it
for nhsat in model.nhsats.values():
    ref = nhsat.parent_ref
    ns_ref = f"{nhsat.namespace}.{ref}" if nhsat.namespace else ref
    if (
        ref not in model.hubs
        and ref not in model.links
        and ns_ref not in model.hubs
        and ns_ref not in model.links
    ):
        errors.append(ResolverError(
            message=f"NhSat '{nhsat.qualified_name}' references unknown parent '{ref}'"
        ))
```

**Pattern 4: SQL Jinja template — MERGE INTO** (new, per D-03)

nhsat template uses MERGE with `parent_hk` as match key. No `load_end_ts` or `hash_diff` — this is current-state-only.

```sql
-- nhsat.sql.j2
-- NhSat: {{ nhsat.name }} (parent: {{ nhsat.parent_ref }})
-- Generated by DMJEDI (non-historized: MERGE/overwrite semantics)

MERGE INTO {{ nhsat.name }} AS target
USING src_{{ nhsat.name }} AS source
ON target.{{ nhsat.parent_ref }}_hk = source.{{ nhsat.parent_ref }}_hk
WHEN MATCHED THEN
    UPDATE SET
        target.load_ts = source.load_ts,
        target.record_source = source.record_source{% if nhsat.columns %},{% endif %}
{%- for col in nhsat.columns %}
        target.{{ col.name }} = source.{{ col.name }}{% if not loop.last %},{% endif %}
{%- endfor %}
WHEN NOT MATCHED THEN
    INSERT ({{ nhsat.parent_ref }}_hk, load_ts, record_source{% if nhsat.columns %}, {% endif %}{% for col in nhsat.columns %}{{ col.name }}{% if not loop.last %}, {% endif %}{% endfor %})
    VALUES (source.{{ nhsat.parent_ref }}_hk, source.load_ts, source.record_source{% if nhsat.columns %}, {% endif %}{% for col in nhsat.columns %}source.{{ col.name }}{% if not loop.last %}, {% endif %}{% endfor %});
```

nhlink template uses MERGE with `link_hk` as match key. Per D-05, the link_hk is computed from hub references (same as historized link).

**Pattern 5: Spark DLT generator — dlt.apply_changes()** (new, per D-04)

`dlt.apply_changes()` is the Databricks DLT API for SCD Type 1 (overwrite). Key parameters:
- `target`: destination table name
- `source`: source dataset name
- `keys`: list of key columns to match on (the hash key)
- `sequence_by`: ordering column to determine which record wins (use `load_ts`)
- `stored_as_scd_type`: set to `1` for overwrite/current-state semantics

The pattern differs structurally from `@dlt.table` — `apply_changes()` is called directly, not used as a decorator. It requires two functions: one to define the target table schema, one to apply changes.

```python
# nhsat Spark DLT pattern (Claude's discretion for exact apply_changes params — D-04)
@dlt.table(
    name="nhsat_{nhsat.name}",
    comment="NhSat: {nhsat.name} (parent: {nhsat.parent_ref}) — current-state"
)
def nhsat_{nhsat.name}_target():
    """Schema definition for non-historized satellite."""
    pass  # Schema inferred from apply_changes target

dlt.apply_changes(
    target="nhsat_{nhsat.name}",
    source="src_{nhsat.name}",
    keys=["{nhsat.parent_ref}_hk"],
    sequence_by=F.col("load_ts"),
    stored_as_scd_type=1,
)
```

Note: The exact `apply_changes()` invocation pattern is under Claude's discretion per CONTEXT.md. The above is the standard Databricks DLT SCD Type 1 pattern. [ASSUMED — based on training knowledge of Databricks DLT API; should be validated against official Databricks docs before final implementation]

**Pattern 6: SqlJinjaGenerator wiring** (from `generator.py`)

Follows exact same structure as existing sat/link wiring:
```python
# src/dmjedi/generators/sql_jinja/generator.py — add after link section
nhsat_tpl = env.get_template("nhsat.sql.j2")
for nhsat in model.nhsats.values():
    result.add_file(f"satellites/nhsat_{nhsat.name}.sql", nhsat_tpl.render(nhsat=nhsat))

nhlink_tpl = env.get_template("nhlink.sql.j2")
for nhlink in model.nhlinks.values():
    result.add_file(f"links/nhlink_{nhlink.name}.sql", nhlink_tpl.render(nhlink=nhlink))
```

**Pattern 7: SparkDeclarativeGenerator wiring**

Follows exact same structure as existing satellite/link methods:
```python
# src/dmjedi/generators/spark_declarative/generator.py — extend generate()
for nhsat in model.nhsats.values():
    result.add_file(f"satellites/nhsat_{nhsat.name}.py", self._generate_nhsat(nhsat))
for nhlink in model.nhlinks.values():
    result.add_file(f"links/nhlink_{nhlink.name}.py", self._generate_nhlink(nhlink))
```

### Recommended Project Structure Changes

```
src/dmjedi/
├── model/
│   ├── core.py              # ADD: NhSat, NhLink classes + DataVaultModel fields
│   └── resolver.py          # ADD: nhsat/nhlink resolution + nhsat parent validation
└── generators/
    ├── spark_declarative/
    │   └── generator.py     # ADD: _generate_nhsat(), _generate_nhlink() methods + wiring
    └── sql_jinja/
        ├── generator.py     # ADD: nhsat/nhlink template loading + wiring
        └── templates/
            ├── nhsat.sql.j2  # NEW: MERGE INTO template for nhsat
            └── nhlink.sql.j2 # NEW: MERGE INTO template for nhlink

tests/
├── test_model.py            # ADD: NhSat/NhLink domain class tests, resolver tests
├── test_generators.py       # ADD: nhsat/nhlink generator output tests
└── fixtures/
    └── nhsat_nhlink.dv      # NEW: test fixture file
```

### Anti-Patterns to Avoid

- **Subclassing Satellite/Link for NhSat/NhLink:** D-01 locks separate classes. Subclassing would break generator dispatch and type narrowing.
- **Adding `is_non_historized` flag to Satellite/Link:** D-01 and D-02 lock separate dicts. Flag-based dispatch was explicitly rejected.
- **Using `@dlt.table` decorator pattern for nhsat/nhlink Spark output:** Non-historized entities require `dlt.apply_changes()` which has a different invocation pattern. Do not reuse `_generate_satellite()` with minor modifications.
- **Reusing sat.sql.j2 / link.sql.j2 with conditionals:** D-09 locks separate template files. MERGE is structurally different from CREATE TABLE + INSERT — a conditional in the existing template would be confusing.
- **Skipping nhsat parent validation in post-resolution pass:** The existing satellite validation block iterates `model.satellites`. A new block for `model.nhsats` must be added explicitly — the existing block will not cover it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SCD Type 1 / overwrite in Spark | Custom MERGE logic in PySpark | `dlt.apply_changes(stored_as_scd_type=1)` | Databricks DLT handles ordering, deduplication, and atomicity |
| Hash key computation | Custom SHA logic | Reuse same `F.sha2(F.concat_ws("||", ...))` pattern from existing generators | Already battle-tested in sat/link generators |
| Type mapping for nhsat/nhlink columns | New type map | Reuse `map_pyspark_type()` and `map_type()` from `model/types.py` | Single source of truth — already handles all 11 DVML types |
| Duplicate detection in resolver | Custom dict check | Reuse `if qname in model.nhsats:` pattern | Already established and tested |

**Key insight:** Every technical problem in this phase is already solved by a pattern in the codebase. The work is replication and adaptation, not invention.

---

## Common Pitfalls

### Pitfall 1: nhsat parent validation not added to post-resolution pass
**What goes wrong:** nhsat with an invalid parent_ref silently resolves to a model with a dangling reference. Generators then emit code referencing non-existent tables.
**Why it happens:** The existing post-resolution validation block in `resolver.py` iterates `model.satellites`, not `model.nhsats`. Easy to forget to add a parallel block.
**How to avoid:** Add a separate post-resolution loop for `model.nhsats.values()` after the existing satellite validation block.
**Warning signs:** Test `test_invalid_nhsat_parent_ref_raises` passes on the existing satellite check but the nhsat check is missing.

### Pitfall 2: MERGE SQL trailing comma in column lists
**What goes wrong:** SQL MERGE template produces invalid SQL like `UPDATE SET col1 = v1, )` when nhsat has no user columns.
**Why it happens:** The `satellite.sql.j2` template uses `{% if sat.columns %},{% endif %}` to handle the empty case — the nhsat template must replicate this carefully for both UPDATE SET and INSERT sections.
**How to avoid:** Test with both an empty-columns nhsat and a multi-column nhsat. The `_assert_valid_sql()` helper in `test_generators.py` checks for this.
**Warning signs:** `_assert_valid_sql(sql)` assertion fails on `,)` check.

### Pitfall 3: apply_changes() requires target table to be defined first
**What goes wrong:** Databricks DLT raises an error at runtime because `apply_changes()` references a target table that was never declared.
**Why it happens:** Unlike `@dlt.table`, the `apply_changes()` pattern requires a preceding `@dlt.table` definition that establishes the target schema (or lets DLT infer it).
**How to avoid:** The generated `.py` file for nhsat/nhlink must include both a `@dlt.table` stub (or schema definition) and the `apply_changes()` call. Check Databricks docs to confirm whether the schema stub is required or optional when `apply_changes()` is the only writer. [ASSUMED — see Assumptions Log A1]
**Warning signs:** Generated code has `apply_changes()` with no preceding `@dlt.table` definition for the same target name.

### Pitfall 4: NhLink model_validator error message inconsistency
**What goes wrong:** Tests checking for "at least 2 hubs" error message fail because NhLink's validator uses a slightly different message than Link's.
**Why it happens:** Copy-paste of Link validator uses the same message string "Link '...' must reference" which is confusing for NhLink.
**How to avoid:** Use "NhLink '...' must reference at least 2 hubs" in the NhLink validator. Update test assertions accordingly.
**Warning signs:** Test `test_nhlink_requires_two_refs` passes but error message doesn't match `NhLink`.

### Pitfall 5: Forgetting to update resolver import line
**What goes wrong:** `resolver.py` imports `Hub, Link, Satellite` from `core` — NhSat and NhLink must be added to that import or a `NameError` occurs at runtime.
**Why it happens:** The import at line 6 of resolver.py is specific. Easy to add domain classes to core.py but forget the resolver import.
**How to avoid:** Check resolver.py imports as the first verification step after adding NhSat/NhLink to core.py.

---

## Code Examples

### Verified Patterns from Codebase

**Link model_validator (exact pattern for NhLink):**
```python
# Source: src/dmjedi/model/core.py lines 49-54 [VERIFIED: Read tool]
@model_validator(mode="after")
def _check_min_refs(self) -> "Link":
    if len(self.hub_references) < 2:
        msg = f"Link '{self.name}' must reference at least 2 hubs"
        raise ValueError(msg)
    return self
```

**Resolver satellite parent validation (exact pattern for nhsat):**
```python
# Source: src/dmjedi/model/resolver.py lines 111-128 [VERIFIED: Read tool]
for sat in model.satellites.values():
    ref = sat.parent_ref
    ns_ref = f"{sat.namespace}.{ref}" if sat.namespace else ref
    if (
        ref not in model.hubs
        and ref not in model.links
        and ns_ref not in model.hubs
        and ns_ref not in model.links
    ):
        errors.append(ResolverError(
            message=f"Satellite '{sat.qualified_name}' references unknown parent '{ref}'"
        ))
```

**SqlJinjaGenerator template wiring (exact pattern for nhsat/nhlink):**
```python
# Source: src/dmjedi/generators/sql_jinja/generator.py lines 33-44 [VERIFIED: Read tool]
sat_tpl = env.get_template("satellite.sql.j2")
for sat in model.satellites.values():
    result.add_file(f"satellites/{sat.name}.sql", sat_tpl.render(sat=sat))
```

**Spark generator _generate_satellite() structure (pattern to adapt for nhsat):**
```python
# Source: src/dmjedi/generators/spark_declarative/generator.py lines 49-85 [VERIFIED: Read tool]
def _generate_satellite(self, sat: Satellite) -> str:
    table_name = f"sat_{sat.name}"
    # ... builds col_selects, hash_diff_line ...
    return (
        f"{_IMPORTS}\n\n"
        f"@dlt.table(\n"
        f'    name="{table_name}",\n'
        # ...
    )
```

**Satellite SQL template structure (adapt for MERGE in nhsat):**
```jinja
{# Source: src/dmjedi/generators/sql_jinja/templates/satellite.sql.j2 [VERIFIED: Read tool] #}
CREATE TABLE IF NOT EXISTS {{ sat.name }} (
    {{ sat.parent_ref }}_hk BINARY NOT NULL,
    ...
    hash_diff BINARY NOT NULL{% if sat.columns %},{% endif %}
{%- for col in sat.columns %}
    {{ col.name }} {{ map_type(col.data_type) }}{% if not loop.last %},{% endif %}
{%- endfor %}
);
```

Note: nhsat.sql.j2 does NOT include `hash_diff` or `load_end_ts` — those are historized-only fields. nhsat is current-state: just the key, `load_ts`, `record_source`, and user columns.

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| INSERT historized records | MERGE INTO / dlt.apply_changes() for current-state | Phase 8 adds the non-historized path |
| Satellite subclassing | Separate NhSat/NhLink classes (D-01) | Cleaner generator dispatch |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `dlt.apply_changes()` with `stored_as_scd_type=1` is the canonical Databricks DLT SCD Type 1 API, and the generated file should include both a `@dlt.table` target definition stub and the `apply_changes()` call | Architecture Patterns — Pattern 5 | Generated Spark code may not execute correctly in Databricks; easy to fix in generated template without schema changes |
| A2 | nhsat does not include `hash_diff` or `load_end_ts` columns (those are historized-only) | Code Examples | If wrong, nhsat is missing required DV2.1 fields; this is a Data Vault modeling question, not a code question |

**Note on A1:** The CONTEXT.md specifies D-04 as a locked decision (`dlt.apply_changes()` with `stored_as_scd_type=1`). The exact parameter list (whether `track_history=False` is needed, whether `@dlt.table` stub is required) is Claude's discretion. Validating against Databricks docs before implementation is recommended.

---

## Open Questions

1. **Does `dlt.apply_changes()` require a preceding `@dlt.table` definition?**
   - What we know: D-04 locks the use of `apply_changes()` with `stored_as_scd_type=1`
   - What's unclear: Whether the generated `.py` file needs a schema stub `@dlt.table` function before `apply_changes()`, or whether `apply_changes()` can be the sole declaration
   - Recommendation: Check Databricks DLT docs; if stub is required, the `_generate_nhsat()` and `_generate_nhlink()` methods emit both stub + `apply_changes()` call. This does not affect any other layer.

2. **Should `track_history=False` be passed to `apply_changes()`?**
   - What we know: `stored_as_scd_type=1` is the primary control; `track_history` may be a redundant/alias parameter
   - What's unclear: Whether `track_history=False` is needed alongside `stored_as_scd_type=1`, or if one implies the other
   - Recommendation: Default to not passing `track_history` unless Databricks docs indicate it is needed for correct SCD Type 1 behavior.

---

## Environment Availability

Step 2.6: SKIPPED — this phase is code/config changes only (no external CLI tools, databases, or services beyond the project's own Python environment). All required libraries (`pydantic`, `lark`, `jinja2`) are already project dependencies verified by the 111-test passing suite.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (version in pyproject.toml) |
| Config file | none — pytest auto-discovers |
| Quick run command | `uv run pytest tests/test_model.py tests/test_generators.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENTITY-03 | NhSat domain class exists with correct fields | unit | `uv run pytest tests/test_model.py -k nhsat -x` | ❌ Wave 0 |
| ENTITY-03 | NhSat parses + resolves with valid parent → in model.nhsats | unit | `uv run pytest tests/test_model.py -k nhsat -x` | ❌ Wave 0 |
| ENTITY-03 | NhSat with invalid parent raises ResolverErrors | unit | `uv run pytest tests/test_model.py -k nhsat -x` | ❌ Wave 0 |
| ENTITY-04 | NhLink domain class enforces 2-hub minimum (model_validator) | unit | `uv run pytest tests/test_model.py -k nhlink -x` | ❌ Wave 0 |
| ENTITY-04 | NhLink parses + resolves with 2+ refs → in model.nhlinks | unit | `uv run pytest tests/test_model.py -k nhlink -x` | ❌ Wave 0 |
| GEN-03 | SQL Jinja generates nhsat file in satellites/ with MERGE INTO | unit | `uv run pytest tests/test_generators.py -k nhsat -x` | ❌ Wave 0 |
| GEN-03 | SQL Jinja generates nhlink file in links/ with MERGE INTO | unit | `uv run pytest tests/test_generators.py -k nhlink -x` | ❌ Wave 0 |
| GEN-03 | Spark DLT generates nhsat file using apply_changes not @dlt.table | unit | `uv run pytest tests/test_generators.py -k nhsat -x` | ❌ Wave 0 |
| GEN-03 | Spark DLT generates nhlink file using apply_changes not @dlt.table | unit | `uv run pytest tests/test_generators.py -k nhlink -x` | ❌ Wave 0 |
| GEN-03 | SQL MERGE output has no trailing commas (structural validity) | unit | `uv run pytest tests/test_generators.py -k nhsat or nhlink -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_model.py tests/test_generators.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green (`uv run pytest` — all 111 existing tests must still pass plus new tests)

### Wave 0 Gaps
- [ ] `tests/test_model.py` — add `test_nhsat_*` and `test_nhlink_*` test functions (extend existing file)
- [ ] `tests/test_generators.py` — add nhsat/nhlink generator output assertion functions (extend existing file)
- [ ] `tests/fixtures/nhsat_nhlink.dv` — new fixture file with nhsat + nhlink declarations for integration tests (optional but recommended for test_integration.py coverage)

*(Framework install: none — pytest already installed and running)*

---

## Security Domain

No security-relevant surface area in this phase. Phase 8 adds code generation logic for two new entity types. Generated output is inert text files — no authentication, session management, access control, cryptography, or input validation (inputs are already parsed/validated by the Lark grammar layer before reaching the resolver).

If `security_enforcement` is enabled at the project level: V5 Input Validation is satisfied by the Lark grammar + Pydantic model_validator on NhLink (enforces 2-hub minimum). No new attack surface is introduced.

---

## Sources

### Primary (HIGH confidence)
- `src/dmjedi/lang/ast.py` — NhSatDecl, NhLinkDecl, DVMLModule.nhsats/nhlinks confirmed [VERIFIED: Read tool]
- `src/dmjedi/lang/parser.py` — nhsat_decl, nhlink_decl transformer methods confirmed [VERIFIED: Read tool]
- `src/dmjedi/lang/grammar.lark` — nhsat_decl and nhlink_decl grammar rules (lines 65-71) confirmed [VERIFIED: Read tool]
- `src/dmjedi/model/core.py` — Hub, Satellite, Link, DataVaultModel class shapes confirmed [VERIFIED: Read tool]
- `src/dmjedi/model/resolver.py` — full resolver loop and validation patterns confirmed [VERIFIED: Read tool]
- `src/dmjedi/generators/spark_declarative/generator.py` — _generate_satellite(), _generate_link() patterns confirmed [VERIFIED: Read tool]
- `src/dmjedi/generators/sql_jinja/generator.py` — template wiring pattern confirmed [VERIFIED: Read tool]
- `src/dmjedi/generators/sql_jinja/templates/satellite.sql.j2` — INSERT template structure confirmed [VERIFIED: Read tool]
- `src/dmjedi/generators/sql_jinja/templates/link.sql.j2` — INSERT template structure confirmed [VERIFIED: Read tool]
- `src/dmjedi/model/types.py` — map_type(), map_pyspark_type(), all 11 DVML types confirmed [VERIFIED: Read tool]
- `tests/test_generators.py` — _assert_valid_sql(), test patterns confirmed [VERIFIED: Read tool]
- `tests/test_model.py` — resolver test patterns confirmed [VERIFIED: Read tool]
- Baseline test run: 111 tests pass [VERIFIED: Bash — uv run pytest]

### Tertiary (LOW confidence / ASSUMED)
- `dlt.apply_changes()` with `stored_as_scd_type=1` parameter — Databricks DLT SCD Type 1 API [ASSUMED — training knowledge, not verified against current Databricks docs in this session]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified by passing test suite
- Domain model design: HIGH — exact patterns read from source, decisions locked in CONTEXT.md
- Resolver extension: HIGH — exact loop patterns read from source
- SQL Jinja templates: HIGH — existing templates read, MERGE pattern follows D-03
- Spark DLT generator: MEDIUM — `apply_changes()` parameter details are ASSUMED (A1)
- Pitfalls: HIGH — based on direct code inspection

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable codebase, no fast-moving dependencies)
