# Generated Example Outputs

This directory contains checked-in output generated from the canonical source model:

- `examples/sales-domain.dv`

Target folders:

- `duckdb` — SQL Jinja output generated with `--dialect duckdb`
- `databricks` — SQL Jinja output generated with `--dialect databricks`
- `postgres` — SQL Jinja output generated with `--dialect postgres`
- `spark-batch` — Spark Declarative output generated with `--mode batch`
- `spark-streaming` — Spark Declarative output generated with `--mode streaming`

## Regenerate

```bash
.venv/bin/dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect duckdb --output examples/generated/duckdb
.venv/bin/dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect databricks --output examples/generated/databricks
.venv/bin/dmjedi generate examples/sales-domain.dv --target sql-jinja --dialect postgres --output examples/generated/postgres
.venv/bin/dmjedi generate examples/sales-domain.dv --target spark-declarative --mode batch --output examples/generated/spark-batch
.venv/bin/dmjedi generate examples/sales-domain.dv --target spark-declarative --mode streaming --output examples/generated/spark-streaming
```

## What To Expect

- SQL targets include `hubs/`, `links/`, `satellites/`, and `staging/` directories.
- Spark targets include `hubs/`, `links/`, and `satellites/` Python files.
- `spark-streaming` differs from `spark-batch` by using `dlt.read_stream(...)` in source-backed raw-vault entities.
