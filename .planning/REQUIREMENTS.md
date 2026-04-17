# Requirements: DMJedi v0.2.0

**Defined:** 2026-04-12
**Core Value:** Data engineers define a model once in DVML and DMJedi generates working, production-ready pipelines for any supported target — from definition to live data warehouse with zero hand-written boilerplate.

## v0.2.0 Requirements

Requirements for v0.2.0 milestone. Each maps to roadmap phases.

### Generator Infrastructure

- [x] **GEN-01**: Generator registry supports parameterized generators via factory pattern (dialect, mode)
- [x] **GEN-02**: SQL templates route all types through dialect-aware helpers (no hardcoded system column types)

### SQL Dialects

- [ ] **DIAL-01**: User can generate DuckDB-compatible SQL from DVML models
- [ ] **DIAL-02**: User can generate Databricks SQL-compatible output from DVML models
- [ ] **DIAL-03**: User can generate PostgreSQL-compatible SQL from DVML models
- [ ] **DIAL-04**: Generated SQL includes hash key columns with dialect-appropriate hash functions
- [ ] **DIAL-05**: Generated SQL uses correct identifier quoting per dialect

### Streaming

- [ ] **STRM-01**: User can generate streaming pipeline output from Spark Declarative generator
- [ ] **STRM-02**: Streaming mode produces DLT streaming table definitions distinct from batch

### LSP Server

- [ ] **LSP-01**: Editor shows parse errors and lint warnings as diagnostics in real-time
- [ ] **LSP-02**: Editor provides keyword completions while typing DVML
- [ ] **LSP-03**: Editor provides entity reference completions (hub names, satellite names, etc.)
- [ ] **LSP-04**: Editor shows entity details on hover (attributes, relationships, source location)
- [ ] **LSP-05**: Editor supports go-to-definition for entity references
- [ ] **LSP-06**: Editor shows document symbol outline for `.dv` files

### LLM Integration

- [ ] **LLM-01**: MCP server exposes validate tool for AI workflows
- [ ] **LLM-02**: MCP server exposes generate tool for AI workflows
- [ ] **LLM-03**: MCP server exposes model explanation tool for AI workflows
- [ ] **LLM-04**: CLI supports `--format json` flag for structured output consumable by LLMs and CI/CD

### Testing

- [x] **TEST-01**: Integration tests execute generated DuckDB SQL against real in-memory DuckDB database
- [x] **TEST-02**: Canonical fixture data exists for all DV2.1 entity types (hubs, sats, links, nhsats, nhlinks, effsats, samlinks, bridges, PITs)
- [x] **TEST-03**: SQLGlot validates syntax of generated Databricks SQL output
- [x] **TEST-04**: Test suite enforces minimum coverage threshold

### Release

- [ ] **REL-01**: Tagged GitHub release with changelog and install instructions
- [ ] **REL-02**: Example DVML models and generated output for all supported targets (DuckDB, Databricks SQL, PostgreSQL, Spark Declarative)

## Future Milestone Requirements

Deferred to later milestones on the road to V1.0.0. Tracked but not in v0.2.0 roadmap.

### Star Schema (v0.3.0+)

- **STAR-01**: User can define dimension and fact tables in DVML
- **STAR-02**: User can generate star schema SQL from DVML models
- **STAR-03**: Slowly changing dimension (SCD) types supported in grammar

### Loading Patterns (v0.3.0+)

- **LOAD-01**: Generated SQL includes INSERT-only loading for hubs
- **LOAD-02**: Generated SQL includes change-detection loading for satellites
- **LOAD-03**: Source-to-target mapping expressible in DVML or config

### IDE Plugins (v1.0.0)

- **IDE-01**: VS Code extension for DVML with syntax highlighting
- **IDE-02**: NeoVim plugin for DVML with TreeSitter grammar

### Advanced UI (v1.0.0)

- **TUI-01**: Terminal UI for interactive model exploration and generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Star Schema modeling | Deferred to v0.3.0+ — ship robust DV2.1 first, architecture supports adding later |
| GUI / web interface | CLI-first tool, not a SaaS product |
| IDE plugins (VS Code, NeoVim extensions) | LSP server in V1 enables this; packaging as extensions is v2 |
| TUI interface | Future release — V1 is CLI-only |
| OAuth / SaaS features | Local developer tool, no network dependencies |
| Plugin marketplace | V1 ships built-in generators only; plugin system exists for future extensibility |
| Loading SQL patterns | High complexity, depends on source-to-target mapping — deferred to v0.3.0+ |
| PyPI publication | v0.2.0 ships as GitHub release; PyPI is a later milestone concern |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GEN-01 | Phase 1: Generator Infrastructure | Satisfied |
| GEN-02 | Phase 1: Generator Infrastructure | Satisfied |
| DIAL-01 | Phase 2: SQL Dialects | Pending |
| DIAL-02 | Phase 2: SQL Dialects | Pending |
| DIAL-03 | Phase 2: SQL Dialects | Pending |
| DIAL-04 | Phase 2: SQL Dialects | Pending |
| DIAL-05 | Phase 2: SQL Dialects | Pending |
| TEST-01 | Phase 3: Integration Testing | Complete |
| TEST-02 | Phase 3: Integration Testing | Complete |
| TEST-03 | Phase 3: Integration Testing | Complete |
| TEST-04 | Phase 3: Integration Testing | Complete |
| LSP-01 | Phase 4: LSP Server | Pending |
| LSP-02 | Phase 4: LSP Server | Pending |
| LSP-03 | Phase 4: LSP Server | Pending |
| LSP-04 | Phase 4: LSP Server | Pending |
| LSP-05 | Phase 4: LSP Server | Pending |
| LSP-06 | Phase 4: LSP Server | Pending |
| LLM-01 | Phase 5: MCP Server & Structured Output | Pending |
| LLM-02 | Phase 5: MCP Server & Structured Output | Pending |
| LLM-03 | Phase 5: MCP Server & Structured Output | Pending |
| LLM-04 | Phase 5: MCP Server & Structured Output | Pending |
| STRM-01 | Phase 6: Streaming & Release | Pending |
| STRM-02 | Phase 6: Streaming & Release | Pending |
| REL-01 | Phase 6: Streaming & Release | Pending |
| REL-02 | Phase 6: Streaming & Release | Pending |

**Coverage:**
- v0.2.0 requirements: 25 total
- Satisfied: 6 (GEN-01, GEN-02, TEST-01, TEST-02, TEST-03, TEST-04)
- Pending: 19
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-04-12*
*Last updated: 2026-04-14 after gap closure phase creation*
