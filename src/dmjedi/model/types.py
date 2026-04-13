"""Shared DVML-to-target type mapping module.

Single source of truth for type conversions used by all generators.
"""
from __future__ import annotations

import re

_PARAM_RE = re.compile(r"^(\w+)\(([^)]*)\)$")

_TYPE_MAP: dict[str, dict[str, str]] = {
    "int": {"default": "INT", "postgres": "INTEGER", "spark": "INT", "duckdb": "INTEGER", "databricks": "INT"},
    "string": {"default": "VARCHAR(255)", "postgres": "TEXT", "spark": "STRING", "duckdb": "VARCHAR", "databricks": "STRING"},
    "decimal": {
        "default": "DECIMAL(18,2)",
        "postgres": "NUMERIC(18,2)",
        "spark": "DECIMAL(18,2)",
        "duckdb": "DECIMAL(18,2)",
        "databricks": "DECIMAL(18,2)",
    },
    "date": {"default": "DATE", "postgres": "DATE", "spark": "DATE", "duckdb": "DATE", "databricks": "DATE"},
    "timestamp": {
        "default": "TIMESTAMP",
        "postgres": "TIMESTAMP",
        "spark": "TIMESTAMP",
        "duckdb": "TIMESTAMP",
        "databricks": "TIMESTAMP",
    },
    "boolean": {"default": "BOOLEAN", "postgres": "BOOLEAN", "spark": "BOOLEAN", "duckdb": "BOOLEAN", "databricks": "BOOLEAN"},
    "json": {"default": "JSON", "postgres": "JSONB", "spark": "STRING", "duckdb": "JSON", "databricks": "STRING"},
    "bigint": {"default": "BIGINT", "postgres": "BIGINT", "spark": "BIGINT", "duckdb": "BIGINT", "databricks": "BIGINT"},
    "float": {"default": "FLOAT", "postgres": "DOUBLE PRECISION", "spark": "FLOAT", "duckdb": "FLOAT", "databricks": "FLOAT"},
    "varchar": {"default": "VARCHAR(255)", "postgres": "VARCHAR(255)", "spark": "STRING", "duckdb": "VARCHAR(255)", "databricks": "STRING"},
    "binary": {"default": "BINARY", "postgres": "BYTEA", "spark": "BINARY", "duckdb": "BLOB", "databricks": "BINARY"},
    # System column types (D-03, D-04)
    # These map system column virtual types to SQL types per dialect.
    # Templates call map_type("hashkey") instead of hardcoding BINARY.
    "hashkey": {
        "default": "BINARY",
        "postgres": "BYTEA",
        "spark": "BINARY",
        "duckdb": "BLOB",
        "databricks": "BINARY",
    },
    "load_ts": {
        "default": "TIMESTAMP",
        "postgres": "TIMESTAMP",
        "spark": "TIMESTAMP",
        "duckdb": "TIMESTAMP",
        "databricks": "TIMESTAMP",
    },
    "record_source": {
        "default": "VARCHAR(255)",
        "postgres": "TEXT",
        "spark": "STRING",
        "duckdb": "VARCHAR",
        "databricks": "STRING",
    },
    "hash_diff": {
        "default": "BINARY",
        "postgres": "BYTEA",
        "spark": "BINARY",
        "duckdb": "BLOB",
        "databricks": "BINARY",
    },
}

_PYSPARK_MAP: dict[str, str] = {
    "int":       "IntegerType()",
    "string":    "StringType()",
    "decimal":   "DecimalType(18, 2)",
    "date":      "DateType()",
    "timestamp": "TimestampType()",
    "boolean":   "BooleanType()",
    "json":      "StringType()",
    "bigint":    "LongType()",
    "float":     "FloatType()",
    "varchar":   "StringType()",
    "binary":    "BinaryType()",
}

# Derive supported dialects from _TYPE_MAP keys (D-08).
# Adding a new dialect key to any _TYPE_MAP entry automatically makes it available in the CLI.
SUPPORTED_DIALECTS: list[str] = sorted(
    {dialect for entry in _TYPE_MAP.values() for dialect in entry}
)


def map_type(dvml_type: str, dialect: str = "default") -> str:
    """Map a DVML type string (possibly with params) to a SQL type for the given dialect.

    Per D-13: parameter-aware. ``varchar(100)`` -> ``VARCHAR(100)`` (default dialect).
    Per D-16: bare ``varchar`` defaults to ``VARCHAR(255)``.
    """
    m = _PARAM_RE.match(dvml_type)
    if m:
        base, params = m.group(1).lower(), m.group(2)
        entry = _TYPE_MAP.get(base)
        if entry:
            base_sql = entry.get(dialect, entry["default"])
            # If the dialect type has no default params and the mapped name differs
            # from the DVML base (e.g., varchar -> STRING for Spark), the target type
            # does not accept parameters — drop them.
            if "(" not in base_sql and base.upper() != base_sql.upper():
                return base_sql
            # Strip default params from base_sql, apply user params
            base_sql_no_params = re.sub(r"\([^)]*\)", "", base_sql)
            return f"{base_sql_no_params}({params})"
        return f"{base.upper()}({params})"
    type_entry = _TYPE_MAP.get(dvml_type.lower())
    if type_entry is None:
        return dvml_type.upper()
    return type_entry.get(dialect, type_entry["default"])


def map_pyspark_type(dvml_type: str) -> str:
    """Map a DVML type string to a PySpark type expression.

    PySpark types ignore parameters (e.g., varchar(100) -> StringType()).
    Exception: decimal preserves precision if specified.
    """
    m = _PARAM_RE.match(dvml_type)
    if m:
        base, params = m.group(1).lower(), m.group(2)
        if base == "decimal":
            return f"DecimalType({params})"
        entry = _PYSPARK_MAP.get(base)
        return entry if entry else f"{base.title()}Type()"
    entry = _PYSPARK_MAP.get(dvml_type.lower())
    return entry if entry else f"{dvml_type.title()}Type()"
