# DMJEDI — Data Modeling Jedi

**CLI for Data Vault 2.1 modeling and data warehouse automation.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

DMJEDI lets data modelers define Data Vault 2.1 models using **DVML** (Data Vault Modeling Language), a purpose-built DSL. The CLI validates models, generates pipeline code (Databricks DLT or SQL), and produces documentation.

## Installation

```bash
# Requires Python 3.11+ and uv
uv pip install -e ".[dev]"
```

## Usage

### Validate models

```bash
# Validate a single file
dmjedi validate examples/sales-domain.dv

# Validate all .dv files in a directory
dmjedi validate examples/

# Validates: syntax, DV2.1 lint rules, and cross-file references
```

### Generate pipeline code

```bash
# Generate SQL DDL for DuckDB
dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect duckdb --output output/duckdb

# Generate SQL DDL for Databricks SQL
dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect databricks --output output/databricks

# Generate SQL DDL for PostgreSQL
dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect postgres --output output/postgres

# Generate Databricks DLT Python (batch)
dmjedi generate examples/sales-domain.dv --target spark-declarative --mode batch --output output/spark-batch

# Generate Databricks DLT Python (streaming)
dmjedi generate examples/sales-domain.dv --target spark-declarative --mode streaming --output output/spark-streaming
```

Checked-in example outputs for all supported targets live under `examples/generated/`.

### Generate documentation

```bash
dmjedi docs examples/sales-domain.dv --output output/docs/
```

## DVML — Data Vault Modeling Language

Write `.dv` files to describe your Data Vault model:

```
namespace sales

hub Customer {
    business_key customer_id : int
}

satellite CustomerDetails of Customer {
    first_name : string
    last_name  : string
    email      : string
}

hub Product {
    business_key product_id : int
}

link CustomerProduct {
    references Customer, Product
}
```

### Multi-file projects

Split models across files using imports:

```
# orders.dv
namespace sales

import "customers.dv"
import "products.dv"

link Order {
    references Customer, Product
    order_date : timestamp
}
```

### Supported types

`int`, `string`, `decimal`, `date`, `timestamp`, `boolean`, `json`

### Validation

DMJEDI validates models at three levels:

1. **Syntax** — Lark parser catches malformed DVML
2. **Lint rules** — DV2.1 rules (hubs need business keys, links need >=2 refs, etc.)
3. **Resolver** — Cross-file checks (duplicate entities, invalid satellite parent references)

## Generator targets

| Target | Flag | Output |
|--------|------|--------|
| SQL (Jinja2) | `--target sql-jinja --dialect duckdb|databricks|postgres` | Dialect-specific `CREATE TABLE` DDL and staging views |
| Spark DLT | `--target spark-declarative --mode batch|streaming` | Databricks DLT Python files with batch or streaming source reads |

SQL generation supports type mapping across dialects (`duckdb`, `databricks`, `postgres`) and Spark Declarative supports both `batch` and `streaming` modes.

Generators are pluggable — implement `BaseGenerator` and register it to add new targets (dbt, Airflow, etc.).

## Architecture

```
.dv files -> parser -> AST -> resolver -> DataVaultModel -> generators -> output
```

```
src/dmjedi/
├── cli/           # Typer CLI (validate, generate, docs)
├── lang/          # DVML grammar (Lark), parser, AST, linter, imports
├── model/         # Resolved Data Vault 2.1 domain model + resolver
├── generators/    # Pluggable code generators
│   ├── spark_declarative/   # Databricks DLT Python
│   └── sql_jinja/           # SQL via Jinja2 templates
├── docs/          # Markdown documentation generator
└── lsp/           # Language Server Protocol (planned)
```

## Development

```bash
uv pip install -e ".[dev]"

pytest                          # Run tests
ruff check . && ruff format .   # Lint & format
mypy src/                       # Type check
```

Release notes live in `CHANGELOG.md`, and the manual ship procedure lives in `docs/release-checklist.md`.

## License

[AGPL-3.0-or-later](LICENSE) — free to use, modify, and distribute. All derivative works must remain open source under the same terms.
