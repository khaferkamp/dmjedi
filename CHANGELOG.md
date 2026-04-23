# Changelog

## v0.2.0

### Highlights

- Multi-dialect SQL generation for DuckDB, Databricks SQL, and PostgreSQL
- Integration testing with DuckDB execution, SQLGlot parsing, and coverage gates
- Structured CLI JSON output and an MCP server with `validate`, `generate`, and `explain`
- Spark Declarative batch and streaming generation modes
- Checked-in generated example outputs for all supported release targets

### Added

#### SQL dialect support

- Added `sql-jinja` dialect generation for `duckdb`, `databricks`, and `postgres`
- Added dialect-aware hash key generation and identifier quoting
- Added staging-view generation for supported physical entity types

#### Integration and quality gates

- Added DuckDB-backed behavioral integration tests over generated SQL
- Added canonical all-entity DVML fixtures and source-row fixtures
- Added SQLGlot validation for generated Databricks SQL
- Enforced an 85% minimum coverage gate in the pytest configuration

#### AI and automation surfaces

- Added `--format json` for `validate`, `generate`, and `docs`
- Added shared application-layer request/result contracts for machine-readable execution
- Added a FastMCP stdio server exposing `validate`, `generate`, and `explain`

#### Spark Declarative streaming

- Added `--mode batch|streaming` to `dmjedi generate`
- Added streaming Spark Declarative output using `dlt.read_stream(...)` for source-backed raw-vault entities
- Added streaming-focused generator, CLI, MCP, and integration test coverage

#### Release assets

- Added checked-in generated example outputs under `examples/generated/`
- Added a manual release checklist under `docs/release-checklist.md`

### Installation

```bash
uv pip install -e ".[dev]"
```

See `README.md` for usage examples and `docs/release-checklist.md` for the final tag/release workflow.

### Deferred from the original milestone roadmap

#### LSP server

- The v0.2.0 roadmap includes an LSP server phase, but the current repository does not yet ship the full LSP implementation described there.
- The CLI still exposes `dmjedi lsp`, and the release notes keep the roadmap item visible so it is not silently lost, but it should be treated as follow-up work rather than a completed v0.2.0 deliverable in the current repo state.
