# Phase 10: Bridge and PIT Tables - Research

**Researched:** 2026-04-08
**Domain:** Data Vault 2.1 query-assist constructs — domain model extension, resolver validation, and view-based code generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Bridge gets a separate class in `core.py` with `path: list[str]`. Validation logic interprets the alternating Hub/Link pattern during resolution.
- **D-02:** `DataVaultModel` gets `bridges: dict[str, Bridge]` as a new field. Follows Phase 8 pattern (separate dicts per entity type).
- **D-03:** PIT gets a separate class in `core.py` with `anchor_ref: str` and `tracked_satellites: list[str]`, mirroring the AST exactly. Validation happens in the resolver.
- **D-04:** `DataVaultModel` gets `pits: dict[str, Pit]` as a new field.
- **D-05:** "Valid chain" means alternating Hub and Link refs: odd positions (0, 2, 4...) must be hubs, even positions (1, 3...) must be links. Path must start and end with a hub. Minimum 3 elements (Hub -> Link -> Hub).
- **D-06:** LINT-04 is a resolver error (not a linter warning). Invalid bridge path blocks resolution.
- **D-07:** Every ref in the bridge path must resolve to an existing entity in the model. Unknown refs are also resolver errors.
- **D-08:** "Belongs to anchor hub" means direct parent match only — each tracked satellite's `parent_ref` must equal the PIT's `anchor_ref` (or its namespace-qualified equivalent). No transitive ownership via links.
- **D-09:** LINT-05 is a resolver error (not a linter warning).
- **D-10:** Only regular satellites (from `model.satellites`) are checked — NhSat, EffSat etc. are not valid PIT tracking targets in this phase.
- **D-11:** SQL Jinja generates `CREATE OR REPLACE VIEW` wrapping a SELECT with JOINs. Bridge joins hubs and links along the path chain. PIT joins hub with satellite snapshots via LEFT JOIN.
- **D-12:** Spark DLT generates `@dlt.view` decorated functions (not `@dlt.table`). Views are recomputed, not stored.
- **D-13:** Output files go in a `views/` directory (e.g., `views/bridge_customer_product.sql`, `views/pit_customer.sql`).
- **D-14:** Future phases will introduce raw vault / business vault directory structures using namespaces. For now, `views/` is the simple starting point.

### Claude's Discretion

- SQL JOIN condition details (hash key matching patterns across dialects)
- PIT snapshot logic (latest record per satellite, temporal join approach)
- Spark DataFrame join implementation details
- SQL Jinja template file names and structure
- Test fixture `.dv` file design for bridge/PIT examples

### Deferred Ideas (OUT OF SCOPE)

- Raw vault / business vault directory organization using namespaces — future phase
- Materialized bridge/PIT options (CREATE TABLE instead of VIEW) — future enhancement
- NhSat/EffSat as valid PIT tracking targets — could extend LINT-05 later
- Strict bridge path connectivity check (verifying links actually reference adjacent hubs) — could strengthen LINT-04 later
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QUERY-01 | User can declare `bridge` with `path` using arrow-chain syntax across hubs and links | Parser + AST already exist. Domain model + resolver needed. |
| QUERY-02 | User can declare `pit` with `of` hub anchor and `tracks` satellite list | Parser + AST already exist. Domain model + resolver needed. |
| LINT-04 | Resolver validates bridge path forms a valid chain through existing entities | Post-resolution validation loop pattern established by Phases 8–9. |
| LINT-05 | Resolver validates PIT satellites belong to the PIT's anchor hub | Same post-resolution pattern; check `satellite.parent_ref == pit.anchor_ref`. |
| GEN-04 | Bridge and PIT generate as views/SELECT (not CREATE TABLE) | SQL Jinja uses `CREATE OR REPLACE VIEW`; Spark uses `@dlt.view`. Both are new to this codebase. |
</phase_requirements>

---

## Summary

Phase 10 adds domain model types (`Bridge`, `Pit`), resolver loops, cross-entity validation, and view-based code generation for bridge and PIT tables. The grammar, AST nodes (`BridgeDecl`, `PitDecl`), and parser transformer methods are fully implemented from Phase 7 — this phase starts at the resolver layer.

The implementation follows a well-established template: Phases 8 and 9 already added four entity types (NhSat, NhLink, EffSat, SamLink) using exactly the same three-step pattern: (1) add domain model class to `core.py` and new dict field to `DataVaultModel`, (2) add resolution loop in `resolver.py` that builds domain objects and deduplicates, (3) add post-resolution validation that checks refs against model dicts. Bridge and PIT fit this template directly. The only novel element is code generation: bridge and PIT produce views, not tables. `CREATE OR REPLACE VIEW` for SQL Jinja and `@dlt.view` for Spark are both new patterns in this codebase — the templates and Spark generator method must express view semantics explicitly.

**Primary recommendation:** Follow the NhSat/NhLink Phase 8 resolver pattern verbatim for the domain model and resolver steps. For generation, use the existing Jinja2 template infrastructure adding two new `.sql.j2` files in `views/`, and add two new `_generate_bridge` / `_generate_pit` methods in the Spark generator. The `views/` output directory requires no infrastructure change — `GeneratorResult.write()` already calls `mkdir(parents=True)`.

---

## Standard Stack

No new library dependencies for this phase. All tools are already installed.

### Core (existing, already in use)

| Library | Purpose | Status |
|---------|---------|--------|
| Pydantic v2 `BaseModel` | Domain model classes (`Bridge`, `Pit`) | [VERIFIED: codebase] |
| Lark (Earley parser) | Grammar and AST — already complete for bridge/PIT | [VERIFIED: codebase] |
| Jinja2 | SQL template rendering via `Environment` + `FileSystemLoader` | [VERIFIED: codebase] |
| pytest | Test framework | [VERIFIED: codebase] |
| ruff | Linting and formatting | [VERIFIED: codebase] |
| mypy (strict) | Type checking | [VERIFIED: codebase] |

**Installation:** No new packages required.

---

## Architecture Patterns

### Existing File Structure to Extend

```
src/dmjedi/
├── lang/
│   ├── ast.py           # BridgeDecl, PitDecl already defined (lines 101, 110)
│   ├── grammar.lark     # bridge_decl, pit_decl rules already defined (lines 84-96)
│   └── parser.py        # transformer methods already complete
├── model/
│   ├── core.py          # ADD: Bridge, Pit classes + DataVaultModel.bridges/pits fields
│   └── resolver.py      # ADD: resolution loops + post-resolution validation
└── generators/
    ├── sql_jinja/
    │   ├── generator.py  # ADD: bridge/pit template rendering in generate()
    │   └── templates/
    │       ├── bridge.sql.j2   # NEW: CREATE OR REPLACE VIEW with JOIN chain
    │       └── pit.sql.j2      # NEW: CREATE OR REPLACE VIEW with LEFT JOINs
    └── spark_declarative/
        └── generator.py  # ADD: _generate_bridge(), _generate_pit() methods

tests/
├── test_model.py          # ADD: Bridge/Pit domain model + resolver tests
├── test_generators.py     # ADD: bridge/pit generation tests
└── fixtures/
    └── bridge_pit.dv      # NEW: fixture for integration testing
```

### Pattern 1: Domain Model Class (copy from Hub/Satellite/EffSat)

**What:** Pydantic `BaseModel` with `name`, `namespace`, `qualified_name` property.
**When to use:** Every new DV entity type.

```python
# Source: src/dmjedi/model/core.py (EffSat pattern, line 94)
class Bridge(BaseModel):
    """A resolved bridge table (query-assist cross-hub traversal)."""

    name: str
    namespace: str = ""
    path: list[str] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


class Pit(BaseModel):
    """A resolved point-in-time table (query-assist snapshot)."""

    name: str
    namespace: str = ""
    anchor_ref: str
    tracked_satellites: list[str] = []

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name
```

`DataVaultModel` extension (after `samlinks`):
```python
# Source: src/dmjedi/model/core.py (DataVaultModel, line 121)
bridges: dict[str, Bridge] = {}
pits: dict[str, Pit] = {}
```

### Pattern 2: Resolver Loop (copy from EffSat pattern, lines 168-190)

**What:** Iterate module declarations, build domain objects, check for duplicates, add to model dict.

```python
# Source: src/dmjedi/model/resolver.py (effsat loop template)
for bridge_decl in module.bridges:
    bridge = Bridge(
        name=bridge_decl.name,
        namespace=ns,
        path=bridge_decl.path,
    )
    qname = bridge.qualified_name
    if qname in model.bridges:
        errors.append(ResolverError(
            message=(
                f"Duplicate bridge '{qname}' redefined"
                f" in {module.source_file or '<string>'}:{bridge_decl.loc.line}"
            ),
            source_file=module.source_file,
            line=bridge_decl.loc.line,
        ))
    else:
        model.bridges[qname] = bridge
```

Same shape for PIT:
```python
for pit_decl in module.pits:
    pit = Pit(
        name=pit_decl.name,
        namespace=ns,
        anchor_ref=pit_decl.anchor_ref,
        tracked_satellites=pit_decl.tracked_satellites,
    )
    # ... duplicate check pattern ...
```

### Pattern 3: Post-Resolution Validation (LINT-04 and LINT-05)

Post-resolution runs after ALL modules are merged so cross-module refs can be resolved.

**LINT-04 — Bridge path validation (D-05, D-06, D-07):**

```python
# Source: codebase analysis [VERIFIED: codebase]
for bridge in model.bridges.values():
    path = bridge.path
    # Rule 1: minimum 3 elements
    if len(path) < 3:
        errors.append(ResolverError(
            message=f"Bridge '{bridge.qualified_name}' path must have at least 3 elements (Hub -> Link -> Hub)"
        ))
        continue
    # Rule 2: alternating Hub/Link pattern
    for i, ref in enumerate(path):
        ns_ref = f"{bridge.namespace}.{ref}" if bridge.namespace else ref
        if i % 2 == 0:  # even positions: must be a hub
            if ref not in model.hubs and ns_ref not in model.hubs:
                errors.append(ResolverError(
                    message=f"Bridge '{bridge.qualified_name}' path position {i} ('{ref}') must be a hub"
                ))
        else:  # odd positions: must be a link
            if ref not in model.links and ns_ref not in model.links:
                errors.append(ResolverError(
                    message=f"Bridge '{bridge.qualified_name}' path position {i} ('{ref}') must be a link"
                ))
```

**LINT-05 — PIT satellite ownership (D-08, D-09, D-10):**

```python
# Source: codebase analysis [VERIFIED: codebase]
for pit in model.pits.values():
    anchor = pit.anchor_ref
    ns_anchor = f"{pit.namespace}.{anchor}" if pit.namespace else anchor
    for sat_ref in pit.tracked_satellites:
        # Look up the satellite in model.satellites only (D-10: not nhsats/effsats)
        sat = model.satellites.get(sat_ref) or model.satellites.get(
            f"{pit.namespace}.{sat_ref}" if pit.namespace else sat_ref
        )
        if sat is None:
            errors.append(ResolverError(
                message=f"PIT '{pit.qualified_name}' tracks unknown satellite '{sat_ref}'"
            ))
        elif sat.parent_ref != anchor and sat.parent_ref != ns_anchor:
            errors.append(ResolverError(
                message=f"PIT '{pit.qualified_name}' satellite '{sat_ref}' does not belong to anchor hub '{anchor}'"
            ))
```

### Pattern 4: SQL Jinja Template — View Pattern (NEW to codebase)

**What:** `CREATE OR REPLACE VIEW` wrapping a SELECT. D-11 mandates this pattern.

**Bridge template** — JOIN chain following path order. Hash keys join adjacent hubs and links:

```jinja2
{# Source: architecture decision D-11, DV2.1 bridge pattern [ASSUMED] #}
-- Bridge: {{ bridge.name }}
-- Generated by DMJEDI (query-assist: view, not table)

CREATE OR REPLACE VIEW bridge_{{ bridge.name }} AS
SELECT
    {{ bridge.path[0] }}.{{ bridge.path[0] }}_hk
    {%- for i in range(1, path|length, 2) %}
    , {{ bridge.path[i] }}.{{ bridge.path[i] }}_hk
    , {{ bridge.path[i+1] }}.{{ bridge.path[i+1] }}_hk
    {%- endfor %}
FROM {{ bridge.path[0] }}
{%- for i in range(1, path|length, 2) %}
JOIN {{ bridge.path[i] }}
    ON {{ bridge.path[i] }}.{{ bridge.path[i-1] }}_hk = {{ bridge.path[i-1] }}.{{ bridge.path[i-1] }}_hk
JOIN {{ bridge.path[i+1] }}
    ON {{ bridge.path[i] }}.{{ bridge.path[i+1] }}_hk = {{ bridge.path[i+1] }}.{{ bridge.path[i+1] }}_hk
{%- endfor %}
;
```

**PIT template** — Hub LEFT JOIN each tracked satellite on hub_hk, latest record per satellite:

```jinja2
{# Source: architecture decision D-11, DV2.1 PIT pattern [ASSUMED] #}
-- PIT: {{ pit.name }} (anchor: {{ pit.anchor_ref }})
-- Generated by DMJEDI (query-assist: view, not table)

CREATE OR REPLACE VIEW pit_{{ pit.name }} AS
SELECT
    h.{{ pit.anchor_ref }}_hk
    , h.load_ts AS snap_load_ts
    {%- for sat in pit.tracked_satellites %}
    , {{ sat }}.load_ts AS {{ sat }}_load_ts
    , {{ sat }}.hash_diff AS {{ sat }}_hash_diff
    {%- endfor %}
FROM {{ pit.anchor_ref }} h
{%- for sat in pit.tracked_satellites %}
LEFT JOIN {{ sat }}
    ON {{ sat }}.{{ pit.anchor_ref }}_hk = h.{{ pit.anchor_ref }}_hk
    AND {{ sat }}.load_ts = (
        SELECT MAX(s2.load_ts) FROM {{ sat }} s2
        WHERE s2.{{ pit.anchor_ref }}_hk = h.{{ pit.anchor_ref }}_hk
    )
{%- endfor %}
;
```

### Pattern 5: Spark DLT View Pattern (NEW to codebase)

**What:** `@dlt.view` decorator instead of `@dlt.table`. D-12 mandates this.

**Bridge:**
```python
# Source: architecture decision D-12, Databricks DLT docs [ASSUMED]
@dlt.view(
    name="bridge_{bridge.name}",
    comment="Bridge: {bridge.name}"
)
def bridge_{bridge.name}():
    """Bridge view traversing: {path_str}."""
    # join chain along path
    df = dlt.read("hub_{path[0]}")
    for i in range(1, len(path), 2):
        link_df = dlt.read("link_{path[i]}")
        hub_df = dlt.read("hub_{path[i+1]}")
        df = df.join(link_df, df["{path[i-1]}_hk"] == link_df["{path[i-1]}_hk"])
        df = df.join(hub_df, df["{path[i+1]}_hk"] == hub_df["{path[i+1]}_hk"])
    return df
```

**PIT:**
```python
# Source: architecture decision D-12 [ASSUMED]
@dlt.view(
    name="pit_{pit.name}",
    comment="PIT: {pit.name} (anchor: {pit.anchor_ref})"
)
def pit_{pit.name}():
    """PIT view anchored on {pit.anchor_ref}."""
    df = dlt.read("hub_{pit.anchor_ref}")
    for sat_ref in pit.tracked_satellites:
        sat_df = dlt.read("sat_{sat_ref}")
        # latest-record window per hub_hk
        window = Window.partitionBy("{pit.anchor_ref}_hk").orderBy(F.col("load_ts").desc())
        sat_latest = sat_df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")
        df = df.join(sat_latest, "{pit.anchor_ref}_hk", "left")
    return df
```

Note: `Window` from `pyspark.sql.window` will need to be imported in the Spark generator.

### Pattern 6: SQL Jinja Generator — Adding New Templates

The generator's `generate()` method follows the established file-per-entity pattern. Add after the existing `nhlink_tpl` block:

```python
# Source: src/dmjedi/generators/sql_jinja/generator.py (existing pattern)
bridge_tpl = env.get_template("bridge.sql.j2")
for bridge in model.bridges.values():
    result.add_file(f"views/bridge_{bridge.name}.sql", bridge_tpl.render(bridge=bridge))

pit_tpl = env.get_template("pit.sql.j2")
for pit in model.pits.values():
    result.add_file(f"views/pit_{pit.name}.sql", pit_tpl.render(pit=pit))
```

### Anti-Patterns to Avoid

- **Using `@dlt.table` for bridge/PIT:** Views are recomputed, not stored. Use `@dlt.view` (D-12).
- **Using `CREATE TABLE IF NOT EXISTS` in SQL template:** Must be `CREATE OR REPLACE VIEW` (D-11).
- **Checking NhSat/EffSat for PIT satellite ownership:** D-10 limits validation to `model.satellites` only.
- **Running bridge path validation inside the resolution loop:** Must run post-resolution so all modules are merged first and cross-module refs can be found (same pattern as satellite parent_ref validation).
- **Skipping minimum-length check before the alternating check:** If `len(path) < 3`, the indexing logic in the alternating check will fail. Add the length guard first and `continue` on failure.
- **Importing `Bridge`/`Pit` in `resolver.py` before adding them to `core.py`:** The domain model must be defined before the resolver can import it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template rendering | String f-string concatenation for SQL | Jinja2 templates (already installed) | Whitespace, comma, and conditional column handling is already solved in existing templates |
| Type checking in post-validation | Custom type registry | Check against `model.hubs` and `model.links` dicts directly | These dicts are the authoritative type registry |
| File output directory creation | Manual `os.makedirs` | `GeneratorResult.write()` already calls `mkdir(parents=True)` | Existing infrastructure handles nested paths |
| Pydantic model construction | `dataclass` or `TypedDict` | `BaseModel` (consistent with all other domain entities) | Validation, serialization, and mypy plugin support |

---

## Common Pitfalls

### Pitfall 1: Bridge Path Namespace Qualification

**What goes wrong:** A bridge path element `Customer` resolves as `test.Customer` in the model dict, but the validation code checks the raw ref `Customer` — lookup fails, spurious error.

**Why it happens:** The same pattern appears in satellite parent_ref validation (lines 232-247 of resolver.py). The fix is already established: check both the raw ref AND the namespace-qualified form (`f"{bridge.namespace}.{ref}"`).

**How to avoid:** Always follow the existing double-check pattern:
```python
if ref not in model.hubs and ns_ref not in model.hubs:
    # error
```

**Warning signs:** Tests pass when bridge/pit are in the same namespace as their referenced entities, but fail when declarations are in different modules.

### Pitfall 2: PIT Satellite Lookup Key

**What goes wrong:** `pit.tracked_satellites` contains raw names like `CustomerDetails`. The `model.satellites` dict is keyed by qualified names like `test.CustomerDetails`. Direct lookup returns `None` and every satellite is flagged as unknown.

**Why it happens:** Same namespace-qualification issue as Pitfall 1, but for satellite lookups.

**How to avoid:** Try both `sat_ref` and `f"{pit.namespace}.{sat_ref}"` as keys, mirroring the parent_ref check pattern in the existing resolver.

### Pitfall 3: Jinja2 Template — `path` as Python List

**What goes wrong:** The bridge template iterates `bridge.path` but the `path` variable is a Python list. Using `range(1, path|length, 2)` in Jinja2 requires `bridge.path|length` (not `path|length`). If the template variable isn't scoped correctly, Jinja2 raises `UndefinedError`.

**How to avoid:** Use consistent variable naming in templates. Bind `path = bridge.path` inside the template using `{% set path = bridge.path %}` or always reference `bridge.path` explicitly.

### Pitfall 4: Spark Generator — `Window` Import

**What goes wrong:** PIT generation uses `Window.partitionBy(...)` from `pyspark.sql.window`. The existing `_IMPORTS` constant in `spark_declarative/generator.py` doesn't include this.

**How to avoid:** Either add `from pyspark.sql.window import Window` to `_IMPORTS`, or include it inline in the generated code string for PIT functions only.

### Pitfall 5: `resolve()` Import List in resolver.py

**What goes wrong:** Adding `Bridge` and `Pit` to `core.py` but forgetting to add them to the import statement at the top of `resolver.py`.

**How to avoid:** The `from dmjedi.model.core import (...)` block (lines 6-16) must be extended. mypy strict mode will catch this if tests are run.

### Pitfall 6: SQL Jinja Generator Import for Bridge/Pit Domain Classes

**What goes wrong:** `sql_jinja/generator.py` imports `DataVaultModel` but not `Bridge` or `Pit` — only needed if type annotations are added to helper methods. The generator accesses these via `model.bridges.values()` which works without explicit imports. No pitfall here, but confirm mypy doesn't complain.

**Warning signs:** mypy errors like `DataVaultModel has no attribute 'bridges'` mean `core.py` wasn't updated. These are type errors, not runtime errors, but will fail the CI lint check.

---

## Code Examples

### Verified: AST Nodes (Phase 7, fully implemented)

```python
# Source: src/dmjedi/lang/ast.py lines 101-117 [VERIFIED: codebase]
class BridgeDecl(BaseModel):
    name: str
    path: list[str] = []  # ordered list of entity refs in the arrow chain
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()

class PitDecl(BaseModel):
    name: str
    anchor_ref: str  # the hub this PIT is anchored to
    tracked_satellites: list[str] = []
    fields: list[FieldDef] = []
    loc: SourceLocation = SourceLocation()
```

### Verified: DVMLModule already has bridges and pits lists

```python
# Source: src/dmjedi/lang/ast.py line 132-133 [VERIFIED: codebase]
bridges: list[BridgeDecl] = []
pits: list[PitDecl] = []
```

### Verified: Grammar rules for bridge and PIT (complete)

```lark
# Source: src/dmjedi/lang/grammar.lark lines 84-96 [VERIFIED: codebase]
bridge_decl: "bridge" IDENTIFIER "{" bridge_body "}"
bridge_body: bridge_member*
bridge_member: path_decl | field_decl
path_decl: "path" path_chain
path_chain: qualified_ref ("->" qualified_ref)+

pit_decl: "pit" IDENTIFIER "{" pit_body "}"
pit_body: pit_member*
pit_member: pit_of | pit_tracks | field_decl
pit_of: "of" qualified_ref
pit_tracks: "tracks" qualified_ref ("," qualified_ref)*
```

### Verified: EffSat resolver loop (template for Bridge/PIT loops)

```python
# Source: src/dmjedi/model/resolver.py lines 168-190 [VERIFIED: codebase]
for effsat_decl in module.effsats:
    effsat = EffSat(
        name=effsat_decl.name,
        namespace=ns,
        parent_ref=effsat_decl.parent_ref,
        columns=[Column(name=f.name, data_type=f.data_type) for f in effsat_decl.fields],
    )
    qname = effsat.qualified_name
    if qname in model.effsats:
        errors.append(ResolverError(
            message=(
                f"Duplicate effsat '{qname}' redefined"
                f" in {module.source_file or '<string>'}:{effsat_decl.loc.line}"
            ),
            source_file=module.source_file,
            line=effsat_decl.loc.line,
        ))
    else:
        model.effsats[qname] = effsat
```

### Verified: Satellite parent_ref post-resolution validation (template for LINT-04/05)

```python
# Source: src/dmjedi/model/resolver.py lines 231-247 [VERIFIED: codebase]
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

### Verified: SQL Jinja generator — adding entity type (template for bridge/PIT blocks)

```python
# Source: src/dmjedi/generators/sql_jinja/generator.py lines 45-56 [VERIFIED: codebase]
nhsat_tpl = env.get_template("nhsat.sql.j2")
for nhsat in model.nhsats.values():
    result.add_file(
        f"satellites/nhsat_{nhsat.name}.sql", nhsat_tpl.render(nhsat=nhsat)
    )
```

### Verified: Test pattern for resolver validation errors

```python
# Source: tests/test_model.py line 75-78 [VERIFIED: codebase]
def test_invalid_parent_ref_raises():
    mod = parse("namespace test\nsatellite Bad of NonExistent { x : string }")
    with pytest.raises(ResolverErrors, match="unknown parent"):
        resolve([mod])
```

### Verified: Test pattern for generator output file naming and content

```python
# Source: tests/test_generators.py lines 50-55 [VERIFIED: codebase]
def test_spark_declarative_generates_files():
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model())
    assert "hubs/Customer.py" in result.files
    assert "satellites/CustomerDetails.py" in result.files
    assert "links/CustomerProduct.py" in result.files
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Manual string building in Spark generator | `@dlt.table` string templates via f-string | Bridge/PIT use `@dlt.view` instead — same f-string approach but different decorator |
| No view outputs | `CREATE OR REPLACE VIEW` for query-assist constructs | New in Phase 10, no existing view template to reuse |

**What's already done and should NOT be reimplemented:**
- Grammar rules (`bridge_decl`, `pit_decl`) — complete [VERIFIED: grammar.lark]
- AST node definitions (`BridgeDecl`, `PitDecl`) — complete [VERIFIED: ast.py]
- Parser transformer methods (`bridge_decl`, `pit_decl`, `bridge_body`, `bridge_member`, `pit_of`, `pit_tracks`, `path_chain`, `path_decl`) — complete [VERIFIED: parser.py]
- `DVMLModule.bridges` and `DVMLModule.pits` list fields — complete [VERIFIED: ast.py]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Bridge SQL template uses `{hub_name}_hk` column naming convention for JOIN conditions | Code Examples / Bridge template | If hk column name differs, JOIN conditions will be wrong — verify against existing hub/link SQL templates |
| A2 | PIT snapshot SQL uses correlated subquery `SELECT MAX(load_ts)` for latest-record logic | Code Examples / PIT template | Could use window functions or a CTE instead — either approach satisfies D-11, difference is performance and dialect compatibility |
| A3 | Spark DLT `@dlt.view` is the correct decorator for non-materialized views | Code Examples / Spark Pattern 5 | If Databricks DLT API uses a different name, generated code won't execute |
| A4 | `Window` and `row_number()` are available in the Spark runtime assumed by the generator | Code Examples / Spark Pattern 5 | PIT Spark generation could use a simpler `groupBy + agg` approach to avoid window dependency |

---

## Open Questions

1. **Bridge SQL template — should table names use prefixed convention?**
   - What we know: SQL tables for hubs are stored as plain `hub.name` (e.g., `Customer`), not `hub_Customer`. Existing templates reference `{{ hub.name }}` directly.
   - What's unclear: Bridge path elements are hub/link names without prefixes. The JOIN will reference `Customer` not `hub_Customer`. This is consistent with existing templates.
   - Recommendation: Use unprefixed names in bridge template, consistent with `hub.sql.j2` and `link.sql.j2`.

2. **PIT template — should `load_end_ts` be included in the satellite snapshot join?**
   - What we know: `satellite.sql.j2` includes `load_end_ts` as a physical column. A PIT view capturing the latest record should filter `WHERE load_end_ts IS NULL` or use `MAX(load_ts)` logic.
   - What's unclear: The exact latest-record pattern is under Claude's discretion (CONTEXT.md).
   - Recommendation: Use `MAX(load_ts)` correlated subquery (dialect-agnostic, works without window function support).

3. **Spark generator — does `@dlt.view` require the `dlt.read()` source to already exist as a DLT table?**
   - What we know: Existing `@dlt.table` functions read from `dlt.read("src_{name}")` staging sources.
   - What's unclear: Bridge/PIT views read from other DLT tables (hub/link/satellite), so they use `dlt.read("hub_Customer")` referencing DLT table names.
   - Recommendation: Use `dlt.read(f"hub_{hub_name}")` convention for reading from upstream DLT tables.

---

## Environment Availability

Step 2.6: SKIPPED (no new external dependencies — all tools already installed, no new CLIs, services, or runtimes required for this phase).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (uses pytest defaults) |
| Quick run command | `pytest tests/test_model.py tests/test_generators.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUERY-01 | `bridge` resolves to `model.bridges` dict with correct `path` | unit | `pytest tests/test_model.py -k "bridge" -x` | ❌ Wave 0 |
| QUERY-02 | `pit` resolves to `model.pits` dict with correct `anchor_ref` and `tracked_satellites` | unit | `pytest tests/test_model.py -k "pit" -x` | ❌ Wave 0 |
| LINT-04 | Invalid bridge path (too short, wrong alternation, unknown ref) raises `ResolverErrors` | unit | `pytest tests/test_model.py -k "bridge" -x` | ❌ Wave 0 |
| LINT-05 | PIT tracking satellite not owned by anchor raises `ResolverErrors` | unit | `pytest tests/test_model.py -k "pit" -x` | ❌ Wave 0 |
| GEN-04 | SQL output uses `CREATE OR REPLACE VIEW`, not `CREATE TABLE`; files in `views/` dir | unit | `pytest tests/test_generators.py -k "bridge or pit" -x` | ❌ Wave 0 |
| GEN-04 | Spark output uses `@dlt.view`, not `@dlt.table`; files in `views/` dir | unit | `pytest tests/test_generators.py -k "bridge or pit" -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_model.py tests/test_generators.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_model.py` — add Bridge/Pit domain model tests and LINT-04/LINT-05 resolver tests (extend existing file)
- [ ] `tests/test_generators.py` — add bridge/PIT generation tests (extend existing file)
- [ ] `tests/fixtures/bridge_pit.dv` — fixture for integration test (optional, DVML example with bridge and pit declarations)

*(No new test framework needed — pytest already configured and running.)*

---

## Security Domain

Security enforcement: no external inputs, no authentication, no network access, no user-supplied data at runtime. This phase generates static SQL/Python files from a parsed domain model. The only input is the DVML source parsed before this phase, and the output is text files written to disk.

No ASVS categories apply to this phase. The applicable security consideration is output path injection (generating files outside the output directory) — mitigated by the existing `GeneratorResult.write()` implementation which uses `output_dir / rel_path` and the `views/` prefix is hard-coded in the generator, not user-controlled.

---

## Sources

### Primary (HIGH confidence)
- `src/dmjedi/lang/ast.py` — BridgeDecl, PitDecl definitions [VERIFIED: codebase]
- `src/dmjedi/lang/grammar.lark` — bridge_decl, pit_decl grammar rules [VERIFIED: codebase]
- `src/dmjedi/lang/parser.py` — transformer methods for bridge/PIT [VERIFIED: codebase]
- `src/dmjedi/model/core.py` — existing domain model classes and DataVaultModel [VERIFIED: codebase]
- `src/dmjedi/model/resolver.py` — resolver loop pattern and post-resolution validation [VERIFIED: codebase]
- `src/dmjedi/generators/sql_jinja/generator.py` — template rendering pattern [VERIFIED: codebase]
- `src/dmjedi/generators/spark_declarative/generator.py` — Spark generation pattern [VERIFIED: codebase]
- `src/dmjedi/generators/sql_jinja/templates/*.sql.j2` — existing SQL Jinja templates [VERIFIED: codebase]
- `tests/test_model.py` — resolver test patterns [VERIFIED: codebase]
- `tests/test_generators.py` — generator test patterns [VERIFIED: codebase]
- `.planning/phases/10-bridge-and-pit-tables/10-CONTEXT.md` — locked decisions [VERIFIED: file]

### Tertiary (LOW confidence — flagged in Assumptions Log)
- A1–A4: SQL JOIN conventions, Spark `@dlt.view` API, PIT snapshot SQL logic — training knowledge, not verified against official Databricks DLT docs in this session

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies verified in codebase, no new packages
- Architecture patterns (resolver + domain model): HIGH — direct copy of established Phase 8/9 patterns verified in source
- Architecture patterns (code generation): MEDIUM — SQL and Spark view patterns are new to this codebase; JOIN logic and `@dlt.view` are [ASSUMED]
- Pitfalls: HIGH — derived from reading the actual resolver code and namespace-qualification pattern
- Test architecture: HIGH — test framework and patterns verified in existing test files

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable codebase — no external API dependencies)
