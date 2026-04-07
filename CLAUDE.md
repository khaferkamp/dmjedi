# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
