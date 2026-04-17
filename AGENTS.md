# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project

DMJEDI is a CLI for Data Vault 2.1 modeling and data warehouse automation. Users write `.dv` files in DVML (Data Vault Modeling Language), and the CLI validates, lints, generates pipeline code, and produces documentation. Licensed AGPL-3.0-or-later.

## Commands

```bash
# Setup (requires uv)
uv venv && uv pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test
pytest tests/test_parser.py::test_parse_hub

# Lint and format
ruff check .
ruff format .

# Type check
mypy src/

# CLI
dmjedi validate examples/sales-domain.dv
dmjedi generate examples/sales-domain.dv --target spark-declarative --output output/
dmjedi generate examples/sales-domain.dv --target sql-jinja --output output/
dmjedi docs examples/sales-domain.dv --output output/docs/
```

## Architecture

The data flow is: `.dv` files → **parser** → AST (`DVMLModule`) → **resolver** → domain model (`DataVaultModel`) → **generators** → output files.

### Processing pipeline

1. **`lang/grammar.lark`** — Lark grammar defining DVML syntax (hubs, satellites, links, namespaces, imports)
2. **`lang/parser.py`** — Parses `.dv` source into `DVMLModule` AST nodes (Pydantic models defined in `lang/ast.py`) using `DVMLTransformer`
3. **`lang/linter.py`** — Validates AST against DV2.1 rules (e.g., hubs need business keys, links need ≥2 refs)
4. **`model/resolver.py`** — Merges multiple `DVMLModule` ASTs into a single `DataVaultModel` (defined in `model/core.py`), keyed by `namespace.EntityName`
5. **Generators** produce output from the resolved `DataVaultModel`

### Generator plugin system

- `generators/base.py` — `BaseGenerator` ABC with `name` property and `generate(model) -> GeneratorResult`
- `generators/registry.py` — Module-level registry; built-in generators auto-register on import
- To add a generator: subclass `BaseGenerator`, implement `name` + `generate`, register in `registry.py`
- Built-in targets: `spark-declarative` (Databricks DLT Python), `sql-jinja` (SQL via Jinja2 templates in `sql_jinja/templates/`)

### Key design decisions

- Two-layer model: **AST** (`lang/ast.py`, parse-tree-shaped, per-file) vs. **domain model** (`model/core.py`, resolved, merged across files). The resolver bridges them.
- `Link` model enforces ≥2 hub references via Pydantic `model_validator`
- All models are Pydantic v2 `BaseModel`s
- DVML uses Lark's Earley parser with `propagate_positions=True` for source locations
- LSP server (`lsp/server.py`) and CLI command wiring are stubs — not yet implemented

## Conventions

- Python ≥3.11, uses `src/` layout with hatchling build backend
- Ruff for linting/formatting (line-length 100), mypy strict mode with pydantic plugin
- Test fixtures go in `tests/fixtures/` (`.dv` files); shared fixtures in `tests/conftest.py`
- DVML types: `int`, `string`, `decimal`, `date`, `timestamp`, `boolean`, `json`
- DVML comments use `#` (shell-style, via Lark's `SH_COMMENT`)

<!-- GSD:project-start source:PROJECT.md -->
## Project

**DMJedi — Data Modelling Jedi**

DMJedi is a CLI tool for declarative data warehouse modeling and automation. Data engineers define models in `.dv` files using DVML (Data Vault Modeling Language), and DMJedi validates, lints, generates pipeline code, and produces documentation. The current milestone (v0.2.0) focuses on multi-dialect SQL generation, LSP server, MCP integration, and battle-tested output for Data Vault 2.1. Future milestones add Star Schema support, loading patterns, and IDE plugins on the road to V1.0.0.

**Core Value:** Data engineers define a model once in DVML and DMJedi generates working, production-ready pipelines for any supported target — from definition to live data warehouse with zero hand-written boilerplate.

### Constraints

- **Python ≥3.11**: Uses `tomllib`, `StrEnum`, modern generics
- **Lark parser**: Earley parser with position propagation — established, not changing
- **Pydantic v2**: All models (AST + domain) — established, not changing
- **AGPL-3.0-or-later**: License is set
- **No external services**: DMJedi is a local tool with no network dependencies at runtime
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- **Python 3.11+** — Primary language (runtime tested on 3.12.12 via uv)
- **Lark grammar** — `src/dmjedi/lang/grammar.lark` defines DVML syntax
- **Jinja2 templates** — `src/dmjedi/generators/sql_jinja/templates/*.sql.j2` for SQL generation
## Runtime & Build
- **Package manager:** uv
- **Build backend:** hatchling
- **Layout:** `src/` layout — source code in `src/dmjedi/`, entry point `dmjedi.cli.main:app`
- **Python version constraint:** `>=3.11` (uses `tomllib`, `StrEnum`, `list[]` generics)
## Core Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| typer | >=0.12 | CLI framework (commands: validate, generate, docs, lsp) |
| pydantic | >=2.0 | All data models (AST nodes + domain model), strict validation |
| lark | >=1.2 | Earley parser for DVML grammar, `propagate_positions=True` |
| jinja2 | >=3.1 | SQL template rendering in sql-jinja generator |
| rich | >=13.0 | Console output formatting, error display |
| pygls | >=1.3 | LSP server framework (stub — not yet implemented) |
## Dev Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0 | Test framework |
| pytest-cov | >=5.0 | Coverage reporting |
| pytest-snapshot | >=0.9 | Snapshot testing for generated output |
| ruff | >=0.4 | Linting + formatting (line-length 100) |
| mypy | >=1.10 | Static type checking (strict mode, pydantic plugin) |
| pre-commit | >=3.7 | Git hook management |
## Configuration
- `pyproject.toml` — Single config file for build, ruff, mypy, pytest
- Ruff rules: `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `RUF`
- Ruff per-file ignore: `B008` in `src/dmjedi/cli/main.py` (typer default args)
- mypy: strict mode with `pydantic.mypy` plugin
- pytest: testpaths `["tests"]`, pythonpath `["src"]`
- No `.env` files, environment variables, or external configuration
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Code Style
- **Line length:** 100 (enforced by ruff)
- **Formatter:** ruff format
- **Linter:** ruff check with rules: `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `RUF`
- **Type checking:** mypy strict mode with pydantic plugin
- **Python target:** 3.11
## Naming
### Python
- **Files:** lowercase_snake_case (`parser.py`, `grammar.lark`)
- **Classes:** PascalCase (`DVMLModule`, `HubDecl`, `DataVaultModel`, `BaseGenerator`)
- **Functions/methods:** snake_case (`parse_file`, `resolve_imports`, `_generate_hub`)
- **Private methods:** prefixed with `_` (`_check_hubs`, `_get_parser`, `_auto_register`)
- **Constants:** UPPER_SNAKE_CASE (`_GRAMMAR_PATH`, `_REGISTRY`, `_IMPORTS`, `_TYPE_MAP`)
- **Test functions:** `test_` prefix, descriptive (`test_parse_hub`, `test_hub_without_business_key`)
### DVML Entity Naming
- Entity types: PascalCase in grammar (`hub Customer`, `satellite CustomerDetails`)
- Keywords: lowercase (`hub`, `satellite`, `link`, `nhsat`, `nhlink`, `effsat`, `samlink`, `bridge`, `pit`)
- Configurable naming prefixes via `.dvml-lint.toml`
## Patterns
### Pydantic Models Throughout
- AST nodes in `lang/ast.py` — flat, field-only models with `SourceLocation`
- Domain model in `model/core.py` — models with `@model_validator`, `@property` for qualified names
- Model validators enforce invariants (e.g., `Link` requires >= 2 hub references)
### Two-Layer Model
- **AST layer** (`lang/ast.py`): Per-file, parse-tree-shaped, uses `Decl` suffix (e.g., `HubDecl`)
- **Domain layer** (`model/core.py`): Resolved, merged across files, no suffix (e.g., `Hub`)
- Resolver bridges the gap with field-by-field mapping
### Generator Plugin Pattern
- ABC `BaseGenerator` with `name` property + `generate()` method
- `GeneratorResult` container holds `dict[str, str]` (path -> content)
- Registry pattern with module-level auto-registration
### CLI Command Pattern
## Error Handling
- **Structured errors:** `ParseError` dataclass with file/line/column/hint
- **Exception wrapping:** `DVMLParseError` wraps `ParseError` for clean message formatting
- **Error collection:** `ResolverErrors` collects all errors before raising (not fail-fast)
- **CLI exits:** `typer.Exit(code=1)` with `from None` to suppress traceback
- **Lint hint catalog:** Maps Lark expected-token sets to human-friendly messages
## Imports
- `from __future__ import annotations` used selectively (not project-wide)
- `TYPE_CHECKING` guard for circular import prevention (e.g., linter importing DataVaultModel)
- Explicit imports preferred over star imports
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern
```
```
## Layers
### 1. Language Layer (`src/dmjedi/lang/`)
- `grammar.lark` — Lark grammar (Earley parser, position propagation)
- `parser.py` — `DVMLTransformer` converts Lark parse tree to Pydantic AST nodes
- `ast.py` — AST node types: `HubDecl`, `SatelliteDecl`, `LinkDecl`, `NhSatDecl`, `NhLinkDecl`, `EffSatDecl`, `SamLinkDecl`, `BridgeDecl`, `PitDecl`, `ImportDecl`, `DVMLModule`
- `linter.py` — Validates AST against DV2.1 rules (hub needs business keys, link needs 2+ refs, effsat parent must be link, naming conventions)
- `imports.py` — Resolves `import` statements via DFS with circular import detection
- `discovery.py` — Finds `.dv` files in paths/directories recursively
### 2. Model Layer (`src/dmjedi/model/`)
- `core.py` — Domain types: `Hub`, `Satellite`, `Link`, `NhSat`, `NhLink`, `EffSat`, `SamLink`, `Bridge`, `Pit`, `DataVaultModel`
- `resolver.py` — `resolve(modules)` merges `DVMLModule` list into single `DataVaultModel`, validates cross-module references (parent refs, bridge paths, PIT satellite ownership)
- `types.py` — Centralized type mapping (DVML types to SQL/PySpark types, dialect-aware)
### 3. Generator Layer (`src/dmjedi/generators/`)
- `base.py` — `BaseGenerator` ABC (`name` property + `generate(model) -> GeneratorResult`)
- `registry.py` — Module-level registry with auto-registration
- `spark_declarative/generator.py` — Generates Databricks DLT Python (hubs, satellites, links, nhsats, nhlinks, effsats, samlinks, bridges, PITs)
- `sql_jinja/generator.py` — Renders SQL via Jinja2 templates with dialect support
- `sql_jinja/templates/` — 9 template files for each entity type
### 4. CLI Layer (`src/dmjedi/cli/`)
- `main.py` — Typer app with commands: `validate`, `generate`, `docs`, `lsp`
- `errors.py` — Rich-formatted error display for parse errors and lint diagnostics
- Each command follows the same pattern: discover -> parse -> lint -> resolve -> act
### 5. Documentation Layer (`src/dmjedi/docs/`)
- `markdown.py` — Generates markdown documentation with Mermaid ER diagrams from `DataVaultModel`
- Groups output into Raw Vault (hubs, links, satellites, etc.) and Query Assist (bridges, PITs)
## Data Flow
### validate command
```
```
### generate command
```
```
### docs command
```
```
## Error Handling
- **Parse errors:** `DVMLParseError` wraps structured `ParseError` (file, line, column, hint). Hint catalog maps Lark expected-token sets to friendly messages.
- **Lint errors:** `LintDiagnostic` with `Severity` enum (ERROR/WARNING/INFO) and rule identifier
- **Resolver errors:** `ResolverErrors` collects all `ResolverError` items (message + source location), raised after full pass
- **CLI:** All errors caught and formatted via Rich console, exit code 1 on errors
## Cross-Cutting Concerns
- **Namespace resolution:** Entities qualified as `namespace.Name`. Resolver checks both bare and qualified forms for references.
- **Validation:** Both AST-level (linter) and model-level (resolver). Linter has model-aware rules (effsat parent check) requiring a second pass post-resolve.
- **Dialect handling:** `--dialect` flag validated against allowlist in CLI. SQL type mapping centralized in `model/types.py`, used by both sql-jinja generator and shared module.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.Codex/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-Codex-profile` -- do not edit manually.
<!-- GSD:profile-end -->
