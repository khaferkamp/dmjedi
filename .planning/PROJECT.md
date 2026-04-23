# DMJedi — Data Modelling Jedi

## What This Is

DMJedi is a local-first CLI for declarative Data Vault 2.1 modeling and warehouse automation. Users define models once in `.dv` files using DVML, and DMJedi validates, lints, documents, and generates production-oriented outputs across SQL dialects, Spark Declarative pipelines, and machine-readable automation interfaces.

## Core Value

Data engineers define a model once in DVML and DMJedi generates working, production-ready pipelines for any supported target — from definition to live data warehouse with zero hand-written boilerplate.

## Current State

- v0.2.0 is shipped and archived.
- Supported generated targets now include DuckDB, Databricks SQL, PostgreSQL, Spark Declarative batch, and Spark Declarative streaming.
- DMJedi exposes a working single-document LSP server plus MCP and JSON automation surfaces for AI and CI workflows.
- The repo includes integration gates against real DuckDB execution, SQLGlot parsing for Databricks SQL, and checked-in generated example outputs.

## Requirements

### Validated

- ✓ Multi-dialect SQL generation for DuckDB, Databricks SQL, and PostgreSQL — v0.2.0
- ✓ Spark Declarative streaming output mode — v0.2.0
- ✓ Single-document LSP server with diagnostics, completions, hover, definition, and symbols — v0.2.0
- ✓ MCP server and shared machine-readable JSON output contracts — v0.2.0
- ✓ Real integration testing with DuckDB execution and SQLGlot parsing gates — v0.2.0
- ✓ Release artifacts: changelog, checklist, and checked-in example output matrix — v0.2.0

### Active

- [ ] Define the next milestone scope
- [ ] Decide whether the next milestone prioritizes Star Schema support, loading patterns, or IDE/editor packaging

### Out of Scope

- GUI / web interface — DMJedi remains CLI-first
- OAuth / SaaS features — local developer tool, no runtime service dependency
- Plugin marketplace / third-party generator distribution — still deferred

## Context

- **Current codebase:** Python 3.11+ monolith with clear parser → AST → resolver → model → generator boundaries, plus LSP and MCP entrypoints.
- **Testing baseline:** full `uv run pytest -x` regression gate passes with coverage above the milestone threshold.
- **Delivery baseline:** release notes, checklist, and generated example outputs now live in-repo and can anchor future milestone ships.

## Constraints

- **Python ≥3.11**
- **Lark Earley parser with position propagation**
- **Pydantic v2 across AST and domain layers**
- **No runtime network dependency**
- **AGPL-3.0-or-later**

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Data Vault only before Star Schema | Keep the first shipped milestone focused and robust | ✓ Good |
| Streaming is a generator concern, not a grammar concern | Preserve DVML target-agnostic modeling | ✓ Good |
| New SQL targets are dialect variants, not separate generators | Keep template and registry complexity low | ✓ Good |
| LSP v0.2.0 stays single-document-only | Ship reliable editor feedback before workspace scope grows | ✓ Good |
| CLI JSON and MCP share one service contract | Prevent automation surfaces from drifting | ✓ Good |
| GitHub release publication remains manual | Keep auth/network edges explicit and reviewable | ✓ Good |

## Next Milestone Goals

- Choose and define the next milestone with `$gsd-new-milestone`
- Likely candidates:
  - Star Schema modeling
  - loading-pattern generation
  - editor packaging beyond the core LSP server

---
*Last updated: 2026-04-23 after v0.2.0 milestone completion*
