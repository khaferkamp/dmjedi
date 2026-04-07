"""DVML to SQL type mapping per dialect."""

from __future__ import annotations

_TYPE_MAP: dict[str, dict[str, str]] = {
    "int": {"default": "INT", "postgres": "INTEGER", "spark": "INT"},
    "string": {"default": "VARCHAR(255)", "postgres": "TEXT", "spark": "STRING"},
    "decimal": {"default": "DECIMAL(18,2)", "postgres": "NUMERIC(18,2)", "spark": "DECIMAL(18,2)"},
    "date": {"default": "DATE", "postgres": "DATE", "spark": "DATE"},
    "timestamp": {"default": "TIMESTAMP", "postgres": "TIMESTAMP", "spark": "TIMESTAMP"},
    "boolean": {"default": "BOOLEAN", "postgres": "BOOLEAN", "spark": "BOOLEAN"},
    "json": {"default": "JSON", "postgres": "JSONB", "spark": "STRING"},
}

SUPPORTED_DIALECTS = ["default", "postgres", "spark"]


def map_type(dvml_type: str, dialect: str = "default") -> str:
    """Map a DVML type to a SQL type for the given dialect."""
    type_entry = _TYPE_MAP.get(dvml_type.lower())
    if type_entry is None:
        return dvml_type.upper()
    return type_entry.get(dialect, type_entry["default"])
