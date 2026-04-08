# Roadmap: DMJEDI

## Milestones

- ✅ **v0.1.0 Complete Core CLI** - Phases 1-6 (shipped)
- 🚧 **v0.1.1 Complete DV 2.1 Entity Coverage** - Phases 7-11 (in progress)

## Phases

<details>
<summary>v0.1.0 Complete Core CLI (Phases 1-6) - SHIPPED</summary>

6 phases, 40 requirements, 75 tests. [Archive](milestones/v0.1.0-ROADMAP.md)

</details>

### v0.1.1 Complete DV 2.1 Entity Coverage

**Milestone Goal:** Extend DVML to support the full Data Vault Alliance 2.1 entity specification with end-to-end pipeline support for all new types, plus parser hardening.

- [ ] **Phase 7: Parser Hardening and Data Types** - Harden the parser foundation and extend the type system before adding new entities
- [ ] **Phase 8: Non-Historized Entities** - Add nhsat and nhlink as the simplest new entity types with full pipeline support
- [ ] **Phase 9: Effectivity Satellites and Same-As Links** - Add the two remaining raw vault entity types with their validation rules
- [x] **Phase 10: Bridge and PIT Tables** - Add the two query-assist constructs with cross-entity validation (completed 2026-04-08)
- [ ] **Phase 11: Output Completeness** - Ensure all generators, docs, and CLI cover all 6 new entity types end-to-end

## Phase Details

### Phase 7: Parser Hardening and Data Types
**Goal**: The parser is fast, gives clear errors, and supports an expanded type system ready for new entities
**Depends on**: Phase 6 (v0.1.0 complete)
**Requirements**: PARSE-01, PARSE-02, PARSE-03, TYPE-01, TYPE-02, TYPE-03
**Success Criteria** (what must be TRUE):
  1. Parsing the same file twice reuses a cached Lark instance (no per-call construction)
  2. A syntax error in a `.dv` file reports the source file path, line number, column, and a human-readable hint
  3. User can declare fields with `bigint`, `float`, `varchar`, and `binary` types and they parse without error
  4. `dmjedi generate` with SQL Jinja produces correct SQL type mappings for the new types across all three dialects
  5. `dmjedi generate` with Spark Declarative produces correct PySpark type mappings for the new types
**Plans:** 2 plans
Plans:
- [x] 07-01-PLAN.md — Parser caching, error reporting, and shared type mapping module
- [x] 07-02-PLAN.md — Grammar rules and AST nodes for 6 new entity types

### Phase 8: Non-Historized Entities
**Goal**: Users can model current-state-only satellites and links that generate MERGE/overwrite patterns instead of historized INSERT
**Depends on**: Phase 7
**Requirements**: ENTITY-03, ENTITY-04, GEN-03
**Success Criteria** (what must be TRUE):
  1. User can declare `nhsat` with `of` referencing a hub or link, and it parses, resolves, and appears in the model
  2. User can declare `nhlink` with `references` to 2+ hubs, and it parses, resolves, and appears in the model
  3. Generated SQL for nhsat and nhlink uses MERGE/overwrite patterns, not INSERT
  4. Generated Spark DLT code for nhsat and nhlink uses overwrite/merge semantics
**Plans:** 2 plans
Plans:
- [x] 08-01-PLAN.md — Domain model classes (NhSat, NhLink) and resolver extension
- [x] 08-02-PLAN.md — SQL Jinja MERGE templates and Spark DLT apply_changes generators

### Phase 9: Effectivity Satellites and Same-As Links
**Goal**: Users can model temporal link validity (effsat) and cross-source entity matching (samlink) with proper validation
**Depends on**: Phase 8
**Requirements**: ENTITY-01, ENTITY-02, LINT-01, LINT-02, LINT-03
**Success Criteria** (what must be TRUE):
  1. User can declare `effsat` with `of` referencing a link and user-declared temporal fields, and it parses and resolves correctly
  2. User can declare `samlink` with `master`/`duplicate` keywords referencing the same hub, and it parses and resolves correctly
  3. Linter warns when an effsat parent is not a link
  4. Linter warns when samlink master and duplicate reference different hubs
  5. Linter warns when entity names violate a configurable naming convention (prefix/suffix)
**Plans:** 2 plans
Plans:
- [x] 09-01-PLAN.md — EffSat and SamLink domain model classes and resolver extension
- [x] 09-02-PLAN.md — Linter rules (LINT-01, LINT-02, LINT-03) and CLI integration

### Phase 10: Bridge and PIT Tables
**Goal**: Users can model query-assist constructs (bridge tables and point-in-time tables) with cross-entity validation
**Depends on**: Phase 9
**Requirements**: QUERY-01, QUERY-02, LINT-04, LINT-05, GEN-04
**Success Criteria** (what must be TRUE):
  1. User can declare `bridge` with `path Hub -> Link -> Hub` arrow-chain syntax, and it parses and resolves correctly
  2. User can declare `pit` with `of` hub anchor and `tracks` satellite list, and it parses and resolves correctly
  3. Resolver validates that a bridge path forms a connected chain through existing hubs and links
  4. Resolver validates that PIT-tracked satellites belong to the PIT's anchor hub
  5. Generated SQL and Spark code for bridge and PIT produce views/SELECT statements, not CREATE TABLE
**Plans:** 2/2 plans complete
Plans:
- [x] 10-01-PLAN.md — Bridge and Pit domain model, resolver loops, LINT-04/LINT-05 validation
- [x] 10-02-PLAN.md — SQL Jinja and Spark DLT view-based code generation for bridge and PIT

### Phase 11: Output Completeness
**Goal**: All generators, documentation, and CLI fully support every new entity type end-to-end
**Depends on**: Phase 10
**Requirements**: GEN-01, GEN-02, DOC-01, DOC-02, CLI-01
**Success Criteria** (what must be TRUE):
  1. `dmjedi generate --target sql-jinja` produces correct SQL for all 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit)
  2. `dmjedi generate --target spark-declarative` produces correct DLT Python for all 6 new entity types
  3. `dmjedi docs` output includes sections for all 6 new entity types
  4. `dmjedi docs` produces Mermaid entity-relationship diagrams covering all entity types
  5. User can pass `--dialect` flag to `dmjedi generate` to select SQL Jinja dialect (default, postgres, spark)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 -> 8 -> 9 -> 10 -> 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Parser Hardening and Data Types | v0.1.1 | 0/2 | Not started | - |
| 8. Non-Historized Entities | v0.1.1 | 0/2 | Not started | - |
| 9. Effectivity Satellites and Same-As Links | v0.1.1 | 0/2 | Not started | - |
| 10. Bridge and PIT Tables | v0.1.1 | 2/2 | Complete    | 2026-04-08 |
| 11. Output Completeness | v0.1.1 | 0/? | Not started | - |
