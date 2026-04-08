# Phase 10: Bridge and PIT Tables - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add resolver support, domain model types, cross-entity validation, and code generation for bridge tables (denormalized cross-hub traversal) and point-in-time tables (snapshot query optimization). Grammar, AST, and parser already exist from Phase 7. Bridge and PIT are query-assist constructs that produce views, not physical tables.

</domain>

<decisions>
## Implementation Decisions

### Bridge Domain Model
- **D-01:** Bridge gets a separate class in `core.py` with `path: list[str]` — flat list of entity refs mirroring the AST. Validation logic interprets the alternating Hub/Link pattern during resolution.
- **D-02:** `DataVaultModel` gets `bridges: dict[str, Bridge]` as a new field. Follows Phase 8 pattern (separate dicts per entity type).

### PIT Domain Model
- **D-03:** PIT gets a separate class in `core.py` with `anchor_ref: str` and `tracked_satellites: list[str]`, mirroring the AST exactly. Validation happens in the resolver.
- **D-04:** `DataVaultModel` gets `pits: dict[str, Pit]` as a new field.

### Bridge Path Validation (LINT-04)
- **D-05:** "Valid chain" means alternating Hub and Link refs: odd positions (0, 2, 4...) must be hubs, even positions (1, 3...) must be links. Path must start and end with a hub. Minimum 3 elements (Hub -> Link -> Hub).
- **D-06:** LINT-04 is a resolver error (not a linter warning). Invalid bridge path blocks resolution. Roadmap says "Resolver validates" — consistent with that wording.
- **D-07:** Every ref in the path must resolve to an existing entity in the model. Unknown refs are also resolver errors.

### PIT Satellite Ownership (LINT-05)
- **D-08:** "Belongs to anchor hub" means direct parent match only — each tracked satellite's `parent_ref` must equal the PIT's `anchor_ref` (or its namespace-qualified equivalent). No transitive ownership via links.
- **D-09:** LINT-05 is a resolver error (not a linter warning). Consistent with LINT-04.
- **D-10:** Only regular satellites (from `model.satellites`) are checked — NhSat, EffSat etc. are not valid PIT tracking targets in this phase.

### Code Generation (GEN-04)
- **D-11:** SQL Jinja generates `CREATE OR REPLACE VIEW` wrapping a SELECT with JOINs. Bridge joins hubs and links along the path chain. PIT joins hub with satellite snapshots via LEFT JOIN.
- **D-12:** Spark DLT generates `@dlt.view` decorated functions (not `@dlt.table`). Views are recomputed, not stored — matches the query-assist semantics.
- **D-13:** Output files go in a `views/` directory (e.g., `views/bridge_customer_product.sql`, `views/pit_customer.sql`). Separates view-based constructs from physical table entities.
- **D-14:** Future phases will introduce raw vault / business vault directory structures using namespaces. For now, `views/` is the simple starting point.

### Claude's Discretion
- SQL JOIN condition details (hash key matching patterns across dialects)
- PIT snapshot logic (latest record per satellite, temporal join approach)
- Spark DataFrame join implementation details
- SQL Jinja template file names and structure
- Test fixture `.dv` file design for bridge/PIT examples

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Parser and AST (Phase 7 output — already built)
- `src/dmjedi/lang/grammar.lark` — Grammar rules for `bridge_decl` (line 85-89) and `pit_decl` (line 92-96), including `path_chain` and `pit_of`/`pit_tracks`
- `src/dmjedi/lang/parser.py` — Transformer methods: `bridge_decl`, `bridge_body`, `bridge_member`, `pit_decl`, `pit_body`, `pit_member`, `pit_of`, `pit_tracks`
- `src/dmjedi/lang/ast.py` — `BridgeDecl` (line 101) and `PitDecl` (line 110) Pydantic models

### Domain Model (extend here)
- `src/dmjedi/model/core.py` — All existing domain classes (Hub, Satellite, Link, NhSat, NhLink, EffSat, SamLink, DataVaultModel)
- `src/dmjedi/model/resolver.py` — Resolver with hub/sat/link/nhsat/nhlink/effsat/samlink loops and post-resolution validation

### Code Generation (extend here)
- `src/dmjedi/generators/sql_jinja/` — SQL Jinja generator with templates per entity type
- `src/dmjedi/generators/spark_declarative/` — Spark DLT generator

### Requirements
- `.planning/REQUIREMENTS.md` — QUERY-01, QUERY-02, LINT-04, LINT-05, GEN-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BridgeDecl` and `PitDecl` AST nodes already defined with all needed fields
- `DVMLModule` already has `bridges` and `pits` lists populated by parser
- Phase 8 NhSat/NhLink pattern provides exact template for domain model + resolver extension
- Phase 9 EffSat/SamLink resolver loop pattern for the entity resolution step
- Existing SQL Jinja templates and Spark generator for reference on output patterns

### Established Patterns
- Domain model classes: Pydantic `BaseModel` with `qualified_name` property
- Resolver loops: iterate `module.{type}s`, build domain object, check duplicates, add to model dict
- Post-resolution validation: check refs exist against model dicts (satellite parent_ref pattern)
- Generator registry: `BaseGenerator` subclass with `name` + `generate()`, auto-registered

### Integration Points
- `DataVaultModel` in `core.py` — add `bridges` and `pits` dicts
- `resolve()` in `resolver.py` — add bridge/pit resolution loops + post-resolution validation for LINT-04 and LINT-05
- SQL Jinja generator — add bridge and PIT templates (CREATE VIEW pattern, new for this codebase)
- Spark DLT generator — add `@dlt.view` functions (new decorator, different from `@dlt.table`)
- Output directory structure — add `views/` subdirectory

</code_context>

<specifics>
## Specific Ideas

- Future phases will introduce raw vault / business vault directory structures using namespaces — for now, `views/` is the simple starting point
- Bridge SQL template: JOIN chain following the path (hub JOIN link ON hk JOIN hub ON hk ...)
- PIT SQL template: hub LEFT JOIN each tracked satellite on hub_hk with latest-record logic

</specifics>

<deferred>
## Deferred Ideas

- Raw vault / business vault directory organization using namespaces — future phase
- Materialized bridge/PIT options (CREATE TABLE instead of VIEW) — future enhancement
- NhSat/EffSat as valid PIT tracking targets — could extend LINT-05 later
- Strict bridge path connectivity check (verifying links actually reference adjacent hubs) — could strengthen LINT-04 later

</deferred>

---

*Phase: 10-bridge-and-pit-tables*
*Context gathered: 2026-04-08*
