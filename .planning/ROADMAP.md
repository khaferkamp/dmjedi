# Roadmap: DMJedi v0.2.0

**Milestone:** v0.2.0
**Created:** 2026-04-12
**Updated:** 2026-04-17 (Phase 03 complete)
**Phases:** 6 (Phase 1 complete, Phases 2-6 from gap closure)

## Phase 1: Generator Infrastructure [COMPLETE]

**Goal:** Establish factory-pattern generator registry, dialect-aware type mapping, and template refactoring for multi-target SQL generation.
**Requirements:** GEN-01, GEN-02
**Status:** Verified — 7/7 verification truths passing, Nyquist compliant

---

## Phase 2: SQL Dialects

**Goal:** Deliver DuckDB, Databricks SQL, and PostgreSQL dialect support with hash keys and correct identifier quoting, building on the type map and registry infrastructure from Phase 1.
**Requirements:** DIAL-01, DIAL-02, DIAL-03, DIAL-04, DIAL-05
**Depends on:** Phase 1 (type map infrastructure, registry factory pattern)
**Gap Closure:** Closes 5 orphaned requirements from milestone audit
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — Type infrastructure (CHAR(64)), hash expression builder, identifier quoting for all DDL templates, existing test updates
- [x] 02-02-PLAN.md — Staging view templates (7 new) and generator wiring for automatic staging view generation
- [x] 02-03-PLAN.md — Comprehensive dialect snapshot tests (27+ DDL + staging snapshots), hash unit tests, all-entity fixture

### Success Criteria
- `dmjedi generate --target sql-jinja --dialect duckdb` produces valid DuckDB SQL
- `dmjedi generate --target sql-jinja --dialect databricks` produces valid Databricks SQL
- `dmjedi generate --target sql-jinja --dialect postgres` produces valid PostgreSQL SQL
- Hash key columns use dialect-appropriate hash functions (e.g., MD5, SHA2)
- Identifier quoting matches dialect convention (backticks, double quotes, etc.)

---

## Phase 3: Integration Testing [COMPLETE]

**Goal:** Validate generated SQL against real databases and enforce quality gates — DuckDB execution tests, canonical fixtures, SQLGlot syntax validation, and coverage thresholds.
**Requirements:** TEST-01, TEST-02, TEST-03, TEST-04
**Depends on:** Phase 2 (needs generated SQL from all dialects to test)
**Gap Closure:** Closes 4 orphaned requirements from milestone audit
**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md — uv/bootstrap setup for DuckDB + SQLGlot dependencies and the 85% pytest-cov gate
- [x] 03-02-PLAN.md — shared canonical source-row fixtures and DuckDB execution helpers for Phase 03 tests
- [x] 03-03-PLAN.md — behavioral DuckDB integration assertions plus full Databricks SQLGlot parsing over generated files

### Success Criteria
- Generated DuckDB SQL executes successfully against in-memory DuckDB
- Fixture `.dv` files cover all 9 DV2.1 entity types
- SQLGlot parses generated Databricks SQL without errors
- pytest-cov enforces minimum coverage threshold in CI config

---

## Phase 4: LSP Server

**Goal:** Implement a Language Server Protocol server providing real-time diagnostics, completions, hover info, go-to-definition, and document symbols for DVML files in any LSP-compatible editor.
**Requirements:** LSP-01, LSP-02, LSP-03, LSP-04, LSP-05, LSP-06
**Depends on:** Phase 1 (parser/linter infrastructure)
**Gap Closure:** Closes 6 orphaned requirements from milestone audit

### Success Criteria
- Parse errors and lint warnings appear as editor diagnostics on save/type
- Keyword completions offered while typing DVML keywords
- Entity references auto-complete from parsed model
- Hover on entity shows attributes, relationships, source location
- Go-to-definition navigates to entity declaration
- Document symbols outline shows all entities in `.dv` file

---

## Phase 5: MCP Server & Structured Output

**Goal:** Expose DMJedi capabilities (validate, generate, explain) as MCP tools for AI workflows, and add `--format json` for structured CLI output consumable by LLMs and CI/CD.
**Requirements:** LLM-01, LLM-02, LLM-03, LLM-04
**Depends on:** Phase 1 (CLI pipeline, parser, generators)
**Gap Closure:** Closes 4 orphaned requirements from milestone audit

### Success Criteria
- MCP server starts and registers validate/generate/explain tools
- `dmjedi validate --format json` outputs structured JSON with errors/warnings
- `dmjedi generate --format json` outputs structured JSON with file contents
- MCP tools return structured responses consumable by AI agents

---

## Phase 6: Streaming & Release

**Goal:** Add streaming pipeline support to the Spark Declarative generator and prepare the v0.2.0 release with changelog, examples, and tagged GitHub release.
**Requirements:** STRM-01, STRM-02, REL-01, REL-02
**Depends on:** Phases 2-5 (all features complete before release)
**Gap Closure:** Closes 4 orphaned requirements from milestone audit

### Success Criteria
- `dmjedi generate --target spark-declarative --mode streaming` produces DLT streaming tables
- Streaming output uses `dlt.read_stream()` / streaming table definitions distinct from batch
- Tagged GitHub release with changelog summarizing all v0.2.0 features
- Example `.dv` models with generated output for DuckDB, Databricks SQL, PostgreSQL, and Spark Declarative

---

*Roadmap updated: 2026-04-17 after executing Phase 03 plan 02*
