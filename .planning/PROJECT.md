# Project: DMJEDI

## Overview

DMJEDI is a CLI for Data Vault 2.1 modeling and data warehouse automation. Users write `.dv` files in DVML (Data Vault Modeling Language), and the CLI validates, lints, generates pipeline code, and produces documentation. Licensed AGPL-3.0-or-later.

## Audience

Team of data engineers using DMJEDI for internal Data Vault projects. Both Databricks/Spark and SQL/dbt platforms are used equally.

## Current State (v0.1.0 + Phase 7)

**Shipped capabilities:**
- Functional CLI: `validate`, `generate`, `docs` commands working end-to-end
- DVML parser with Lark grammar, AST, and 4 lint rules
- Multi-file support: directory discovery, imports with circular detection
- Resolver with duplicate detection and parent ref validation
- SQL Jinja generator with 3 SQL dialect type mappings (default, postgres, spark)
- Spark Declarative generator producing functional Databricks DLT Python
- Markdown documentation generator
- Generator plugin system with registry
- Phase 7 complete: Parser caching (singleton), structured error reporting with Rich, 4 new data types (bigint, float, varchar, binary) with optional parameters, shared type mapping module (model/types.py), grammar + AST for all 6 new entity types (nhsat, nhlink, effsat, samlink, bridge, pit)
- Phase 8 complete: NhSat and NhLink domain model classes, resolver extension with parent validation, SQL Jinja MERGE INTO templates, Spark DLT apply_changes(stored_as_scd_type=1) generators
- Phase 9 complete: EffSat and SamLink domain model classes, resolver extension, linter rules (LINT-01 effsat parent, LINT-02 samlink same-hub, LINT-03 naming convention)
- Phase 10 complete: Bridge and PIT domain model classes, resolver with LINT-04 (bridge path chain validation) and LINT-05 (PIT satellite ownership), SQL Jinja CREATE VIEW templates, Spark DLT @dlt.view generators, views/ output directory
- 173 tests across 8 test files

**Known limitations:**
- LSP server is a placeholder (pygls dependency unused)
- No `--dialect` CLI flag for SQL generator (constructor-only)
- No path traversal protection on imports (dormant — needs implementing when imports go public)

## Current Milestone: v0.1.1 Complete DV 2.1 Entity Coverage

**Goal:** Extend DVML to support the full Data Vault Alliance 2.1 entity specification with end-to-end pipeline support for all new types, plus parser hardening.

**Target features:**
- Effectivity Satellites (temporal validity on link relationships)
- Same-As Links (cross-source entity matching)
- Non-Historized Satellites (current-state-only, no history)
- Non-Historized Links (current-state-only links)
- Bridge Tables (denormalized access patterns)
- Point-in-Time Tables (snapshot query optimization)
- Parser caching (reuse Lark instance)
- Better parse error messages with source locations
- General parser hardening

## Technical Constraints

- Python >=3.11, src/ layout with hatchling
- Pydantic v2 for all models
- Lark Earley parser
- Typer for CLI, Rich for terminal output
- Ruff + mypy strict for quality gates

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after Phase 10 completion*
