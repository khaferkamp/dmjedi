# Project: DMJEDI

## Overview

DMJEDI is a CLI for Data Vault 2.1 modeling and data warehouse automation. Users write `.dv` files in DVML (Data Vault Modeling Language), and the CLI validates, lints, generates pipeline code, and produces documentation for the full DV 2.1 entity specification. Licensed AGPL-3.0-or-later.

## Audience

Team of data engineers using DMJEDI for internal Data Vault projects. Both Databricks/Spark and SQL/dbt platforms are used equally.

## Current State (v0.1.1)

**Shipped capabilities:**
- Functional CLI: `validate`, `generate`, `docs` commands working end-to-end
- DVML parser with Lark grammar, AST, parser caching (singleton), structured error reporting with Rich
- Support for all 9 DV 2.1 entity types: hub, satellite, link, nhsat, nhlink, effsat, samlink, bridge, pit
- 4 data types with optional parameters (bigint, float, varchar, binary) plus core types (int, string, decimal, date, timestamp, boolean, json)
- Multi-file support: directory discovery, imports with circular detection
- Resolver with duplicate detection, parent ref validation, bridge path chain validation (LINT-04), PIT satellite ownership (LINT-05)
- 5 linter rules: hub needs BKs, satellite needs parent, link needs 2+ refs, effsat parent must be link, samlink same-hub, naming conventions (all 9 entity types)
- SQL Jinja generator with 9 entity templates, 3 dialect mappings (default, postgres, spark), `--dialect` CLI flag
- Spark Declarative generator producing Databricks DLT Python for all 9 entity types (@dlt.table, @dlt.view, dlt.apply_changes)
- Markdown documentation generator with Raw Vault / Query Assist grouping and Mermaid ER diagrams
- Generator plugin system with registry
- 202 tests across 10 test files

**Known limitations:**
- LSP server is a placeholder (pygls dependency unused)
- No path traversal protection on imports (dormant — needs implementing when imports go public)

## Milestone History

| Version | Name | Phases | Tests | Status |
|---------|------|--------|-------|--------|
| v0.1.0 | Complete Core CLI | 6 | 75 | Shipped |
| v0.1.1 | Complete DV 2.1 Entity Coverage | 6 | 202 | Shipped |

## Technical Constraints

- Python >=3.11, src/ layout with hatchling
- Pydantic v2 for all models
- Lark Earley parser
- Typer for CLI, Rich for terminal output
- Ruff + mypy strict for quality gates

## Key Decisions

| Decision | Milestone | Outcome |
|----------|-----------|---------|
| Two-layer model (AST vs domain) | v0.1.0 | ✓ Clean separation, resolver bridges cleanly |
| Separate domain classes per entity type | v0.1.1 | ✓ Generator dispatch clean, no type flags needed |
| MERGE for nhsat/nhlink/effsat/samlink | v0.1.1 | ✓ Correct SCD Type 1 semantics |
| CREATE VIEW for bridge/pit | v0.1.1 | ✓ Query-assist constructs are views, not tables |
| Linter rules as warnings, resolver as errors | v0.1.1 | ✓ Appropriate severity levels |
| Naming convention via .dvml-lint.toml | v0.1.1 | ✓ Configurable, optional, project-level |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after v0.1.1 milestone completion*
