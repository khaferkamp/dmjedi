# Milestones

## v0.1.1 Complete DV 2.1 Entity Coverage (Shipped: 2026-04-08)

**Phases completed:** 6 phases, 12 plans, 15 tasks

**Key accomplishments:**

- One-liner:
- 6 new DV 2.1 entity types (nhsat, nhlink, effsat, samlink, bridge, pit) fully parsed via Lark grammar into Pydantic AST nodes, extending DVMLModule to cover all 9 entity types
- One-liner:
- One-liner:
- One-liner:
- Bridge and Pit domain model classes with resolver loops, LINT-04 bridge path chain validation, and LINT-05 PIT satellite ownership validation
- 1. [Rule 3 - Blocking] Added pythonpath to pyproject.toml for worktree isolation
- SQL Jinja MERGE templates and Spark DLT apply_changes generators for EffSat and SamLink entities, completing pipeline code generation for all DV 2.1 current-state entity types
- 1. [Rule 2 - Auto-fix] Removed unused `pytest` import from test file
- --dialect flag added to generate command, wiring user-selected SQL dialect (default/postgres/spark) directly to SqlJinjaGenerator constructor with allowlist validation and non-sql-jinja warning
- LINT-03 bridge/pit naming coverage added to all 9 entity types and docs command model-aware error gate added matching validate/generate behavior

---
