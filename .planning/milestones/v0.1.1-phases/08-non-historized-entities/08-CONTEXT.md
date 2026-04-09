# Phase 8: Non-Historized Entities - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add resolver support, domain model types, and code generation for non-historized satellites (nhsat) and non-historized links (nhlink). These entities use MERGE/overwrite semantics instead of historized INSERT. Grammar and AST nodes already exist from Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Domain Model Design
- **D-01:** NhSat and NhLink get their own separate classes in `model/core.py`, not subclasses of Satellite/Link. Follows pre-roadmap decision for separate types and keeps generator dispatch clean.
- **D-02:** DataVaultModel gets `nhsats: dict[str, NhSat]` and `nhlinks: dict[str, NhLink]` as new fields. Generators iterate separate dicts — no type-checking or flag-filtering needed.

### MERGE/Overwrite SQL Pattern
- **D-03:** SQL output for nhsat/nhlink uses `MERGE INTO` pattern. Template: `MERGE INTO target USING source ON key WHEN MATCHED THEN UPDATE SET ... WHEN NOT MATCHED THEN INSERT (...)`.
- **D-04:** Spark DLT output uses `dlt.apply_changes()` with `stored_as_scd_type=1`. Declarative, fits existing DLT generator pattern.
- **D-05:** MERGE match key is the parent hash key — nhsat matches on `parent_hk`, nhlink matches on its own `link_hk` computed from hub references. Mirrors historized versions.

### Resolver Validation Rules
- **D-06:** nhsat parent_ref validation follows same rules as regular satellite — parent must be an existing hub or link. Same validation logic, same error messages.
- **D-07:** NhLink enforces same minimum 2-hub reference rule as Link, using the same Pydantic `model_validator` pattern.

### Generator Output Layout
- **D-08:** nhsat files go in `satellites/` directory (filename: `nhsat_X.py` or `nhsat_X.sql`). nhlink files go in `links/` directory (filename: `nhlink_X.py` or `nhlink_X.sql`). Same dirs as historized, prefix distinguishes them.
- **D-09:** SQL Jinja uses separate template files: `nhsat.sql.j2` and `nhlink.sql.j2`. MERGE pattern is fundamentally different from INSERT. Follows Phase 7 decision D-11 (explicit, self-contained rules per entity type).

### Claude's Discretion
- Exact `apply_changes()` parameter configuration (sequence_by, track_history, etc.)
- SQL MERGE template variations across dialects (default, postgres, spark)
- Test fixture `.dv` file design for nhsat/nhlink examples
- Whether NhSat/NhLink domain classes share a base mixin for common fields or duplicate them

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Parser and AST (Phase 7 output — already built)
- `src/dmjedi/lang/grammar.lark` — Grammar rules for `nhsat_decl` and `nhlink_decl` (lines 65-71)
- `src/dmjedi/lang/parser.py` — Transformer methods: `nhsat_decl`, `nhlink_decl`, `nhlink_body`, `nhlink_member`
- `src/dmjedi/lang/ast.py` — `NhSatDecl` and `NhLinkDecl` Pydantic models (AST nodes)

### Domain Model (extend here)
- `src/dmjedi/model/core.py` — Hub, Satellite, Link, Column, DataVaultModel classes
- `src/dmjedi/model/resolver.py` — Resolver that merges AST modules into DataVaultModel

### Generators (extend here)
- `src/dmjedi/generators/spark_declarative/generator.py` — Spark DLT generator with `_generate_satellite()`, `_generate_link()` patterns
- `src/dmjedi/generators/sql_jinja/` — SQL Jinja generator with templates in `templates/` subdirectory
- `src/dmjedi/model/types.py` — Shared type mapping module (used by both generators)

### Requirements
- `.planning/REQUIREMENTS.md` — ENTITY-03, ENTITY-04, GEN-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NhSatDecl` and `NhLinkDecl` AST nodes already defined in `ast.py` with fields matching what the domain model needs
- `DVMLModule` already has `nhsats` and `nhlinks` lists populated by the parser
- `_generate_satellite()` and `_generate_link()` patterns in Spark generator can be adapted for nhsat/nhlink
- `sat.sql.j2` and `link.sql.j2` templates provide the base structure to adapt for MERGE patterns
- `map_pyspark_type()` and `map_type()` in `model/types.py` already handle all data types

### Established Patterns
- Domain model classes use Pydantic `BaseModel` with `qualified_name` property
- Link uses `model_validator(mode="after")` for 2-hub minimum — nhlink should replicate
- Resolver loops over `module.{entity_type}s` and builds domain objects with duplicate detection
- Generators iterate `model.{entity_type}s.values()` and call `_generate_{type}()` methods
- SQL Jinja templates are in `generators/sql_jinja/templates/` with `.sql.j2` extension

### Integration Points
- `DataVaultModel` in `core.py` — add `nhsats` and `nhlinks` dicts
- `resolve()` in `resolver.py` — add nhsat/nhlink resolution loops (after existing sat/link)
- `SparkDeclarativeGenerator.generate()` — add nhsat/nhlink iteration
- `SqlJinjaGenerator.generate()` — add nhsat/nhlink iteration
- `BaseGenerator` — no changes needed (generators auto-discover from model)

</code_context>

<specifics>
## Specific Ideas

- `apply_changes()` is Databricks DLT's native SCD Type 1 API — use it instead of manual merge in Spark
- MERGE SQL should follow the standard ANSI pattern so it works across all 3 dialects
- Generated files use `nhsat_` and `nhlink_` prefixes to distinguish from historized versions in the same directory

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-non-historized-entities*
*Context gathered: 2026-04-08*
