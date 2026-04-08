# Phase 11: Output Completeness - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Ensure all generators, documentation, and CLI fully support every new entity type end-to-end. EffSat and SamLink need code generation (deferred from Phase 9). Docs generator needs expansion to all 6 new types plus Mermaid ER diagrams. CLI needs `--dialect` flag.

</domain>

<decisions>
## Implementation Decisions

### EffSat Code Generation
- **D-01:** EffSat SQL uses MERGE INTO pattern (not INSERT). Temporal validity records are updated when validity periods change. Same MERGE shape as nhsat template.
- **D-02:** EffSat Spark DLT uses `dlt.apply_changes(stored_as_scd_type=1)` — MERGE semantics matching the SQL pattern.
- **D-03:** EffSat output files go in `satellites/` directory (filename: `effsat_{name}.sql` or `effsat_{name}.py`). Consistent with nhsat convention from Phase 8.

### SamLink Code Generation
- **D-04:** SamLink SQL uses MERGE INTO pattern. Deduplication relationships may be updated over time.
- **D-05:** SamLink Spark DLT uses `dlt.apply_changes(stored_as_scd_type=1)` — MERGE semantics.
- **D-06:** SamLink output files go in `links/` directory (filename: `samlink_{name}.sql` or `samlink_{name}.py`). Consistent with nhlink convention from Phase 8.

### Docs Generator Expansion (DOC-01)
- **D-07:** Documentation grouped by category: "Raw Vault" (hubs, links, satellites, nhsat, nhlink, effsat, samlink) and "Query Assist" (bridge, pit). Each entity type gets its own subsection with columns table.
- **D-08:** Bridge docs show path chain. PIT docs show anchor hub and tracked satellites list.
- **D-09:** NhSat/NhLink docs show parent ref and columns like their historized counterparts.
- **D-10:** EffSat docs show parent ref (link). SamLink docs show master and duplicate refs.

### Mermaid ER Diagrams (DOC-02)
- **D-11:** Single erDiagram block per model covering all entity types and their relationships.
- **D-12:** Diagram placed at the top of the docs output, before detailed sections. Overview-first layout.
- **D-13:** Relationship notation: satellites use `||--o{`, links connect multiple hubs, effsat attaches to links, samlink shows master/duplicate, bridge/pit use dotted lines (`||..o{`).

### CLI --dialect Flag (CLI-01)
- **D-14:** `--dialect` flag added to the `generate` command. Only applies when `--target sql-jinja`. Choices: `default`, `postgres`, `spark`. Default value: `default`.
- **D-15:** If `--dialect` is used with a non-sql-jinja target (e.g., spark-declarative), emit a warning and ignore the flag. Don't error.
- **D-16:** The existing `SqlJinjaGenerator(dialect=)` constructor parameter is wired to the CLI flag. No changes to generator internals needed.

### Claude's Discretion
- MERGE match key details for effsat and samlink across dialects
- Exact Mermaid relationship cardinality annotations
- `_effsat_section()` and `_samlink_section()` markdown formatting details
- EffSat/SamLink `apply_changes()` parameter tuning (sequence_by, track_history, etc.)
- Test fixture design for effsat/samlink generation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Code Generation (extend here)
- `src/dmjedi/generators/sql_jinja/generator.py` — SqlJinjaGenerator with existing nhsat/nhlink/bridge/pit loops
- `src/dmjedi/generators/sql_jinja/templates/` — All existing .j2 templates (nhsat.sql.j2, nhlink.sql.j2, bridge.sql.j2, pit.sql.j2 as patterns)
- `src/dmjedi/generators/spark_declarative/generator.py` — SparkDeclarativeGenerator with _generate_nhsat, _generate_nhlink, _generate_bridge, _generate_pit methods
- `src/dmjedi/generators/base.py` — BaseGenerator ABC and GeneratorResult

### Domain Model (read-only reference)
- `src/dmjedi/model/core.py` — EffSat, SamLink, Bridge, Pit domain classes
- `src/dmjedi/model/types.py` — map_type() function with per-dialect mapping

### Documentation (extend here)
- `src/dmjedi/docs/markdown.py` — generate_markdown() currently covering hub, link, satellite only

### CLI (extend here)
- `src/dmjedi/cli/main.py` — generate command (needs --dialect), docs command

### Requirements
- `.planning/REQUIREMENTS.md` — GEN-01, GEN-02, DOC-01, DOC-02, CLI-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `nhsat.sql.j2` and `nhlink.sql.j2` templates as patterns for effsat/samlink MERGE templates
- `_generate_nhsat()` and `_generate_nhlink()` Spark methods as patterns for effsat/samlink
- `_hub_section()`, `_satellite_section()`, `_link_section()` in markdown.py as patterns for new entity sections
- `map_type()` in model/types.py already handles per-dialect type mapping
- Existing generator tests in `tests/test_generators.py` as pattern for new tests

### Established Patterns
- SQL Jinja: one template per entity type, generator loops iterate model dict
- Spark DLT: one `_generate_{type}()` method per entity type
- Docs: one `_{type}_section()` function per entity type
- CLI: Typer options with `typer.Option()` decorators

### Integration Points
- `SqlJinjaGenerator.generate()` — add effsat/samlink loops
- `SparkDeclarativeGenerator.generate()` — add effsat/samlink loops
- `generate_markdown()` — restructure into Raw Vault / Query Assist grouping, add 6 new entity sections, add Mermaid diagram generation
- `cli/main.py generate()` — add `--dialect` option, pass to SqlJinjaGenerator constructor
- `generators/registry.py` — may need to pass dialect through to SqlJinjaGenerator

</code_context>

<specifics>
## Specific Ideas

- EffSat MERGE key: parent link hash key (same as nhsat uses parent hub hash key)
- SamLink MERGE key: samlink hash key computed from master_hk + duplicate_hk
- Mermaid erDiagram supports relationship annotations — use entity type labels (satellite, link, effsat, etc.)
- Docs should use `## Raw Vault` and `## Query Assist` as top-level sections, with `###` per entity type category and `####` per individual entity

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-output-completeness*
*Context gathered: 2026-04-08*
