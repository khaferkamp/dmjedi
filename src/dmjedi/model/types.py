"""Shared DVML-to-target type mapping module.

Single source of truth for type conversions used by all generators.
"""
from __future__ import annotations

import re

_PARAM_RE = re.compile(r"^(\w+)\(([^)]*)\)$")

_TYPE_MAP: dict[str, dict[str, str]] = {
    "int": {"default": "INT", "postgres": "INTEGER", "spark": "INT"},
    "string": {"default": "VARCHAR(255)", "postgres": "TEXT", "spark": "STRING"},
    "decimal": {
        "default": "DECIMAL(18,2)",
        "postgres": "NUMERIC(18,2)",
        "spark": "DECIMAL(18,2)",
    },
    "date": {"default": "DATE", "postgres": "DATE", "spark": "DATE"},
    "timestamp": {
        "default": "TIMESTAMP",
        "postgres": "TIMESTAMP",
        "spark": "TIMESTAMP",
    },
    "boolean": {"default": "BOOLEAN", "postgres": "BOOLEAN", "spark": "BOOLEAN"},
    "json": {"default": "JSON", "postgres": "JSONB", "spark": "STRING"},
    "bigint": {"default": "BIGINT", "postgres": "BIGINT", "spark": "BIGINT"},
    "float": {"default": "FLOAT", "postgres": "DOUBLE PRECISION", "spark": "FLOAT"},
    "varchar": {"default": "VARCHAR(255)", "postgres": "VARCHAR(255)", "spark": "STRING"},
    "binary": {"default": "BINARY", "postgres": "BYTEA", "spark": "BINARY"},
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

SUPPORTED_DIALECTS = ["default", "postgres", "spark"]


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
