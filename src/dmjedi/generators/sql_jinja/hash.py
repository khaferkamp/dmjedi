"""Dialect-aware hash expression builder for staging view SQL.

Builds hash expressions with COALESCE NULL handling and
double-pipe delimiter concatenation per Data Vault 2.1 standard.

Hash algorithm is configurable per D-02 (global model-level setting,
not per-dialect). Default is SHA-256.
"""
from __future__ import annotations

# Nested dict: _HASH_FUNCTIONS[dialect][hash_algo] = template_str
# Per D-02: hash algorithm is configurable as a global setting.
# Currently supported algorithm: "sha256". The framework supports
# adding more algorithms by extending the inner dicts.
_HASH_FUNCTIONS: dict[str, dict[str, str]] = {
    "duckdb": {
        "sha256": "sha256({expr})",
    },
    "databricks": {
        "sha256": "sha2({expr}, 256)",
    },
    "postgres": {
        "sha256": "encode(sha256(({expr})::bytea), 'hex')",
    },
    "default": {
        "sha256": "SHA256({expr})",
    },
}


def build_hash_expr(
    columns: list[str],
    dialect: str = "default",
    hash_algo: str = "sha256",
) -> str:
    """Build a hash expression from column names for the given dialect.

    Per D-02: Hash algorithm is configurable (default SHA-256).
    Per D-04: COALESCE to empty string for NULL handling.
    Per D-07: Double-pipe delimiter '||' between business keys.
    Per D-08: Result is a hex string fitting CHAR(64).

    Lookup order for hash function template:
    1. _HASH_FUNCTIONS[dialect][hash_algo]
    2. _HASH_FUNCTIONS["default"][hash_algo]
    3. _HASH_FUNCTIONS["default"]["sha256"]

    Args:
        columns: List of column name strings (unquoted -- quoting is handled
                 by the caller or Jinja2 q filter).
        dialect: SQL dialect key (duckdb, databricks, postgres, default).
        hash_algo: Hash algorithm name (default: "sha256").

    Returns:
        Complete SQL hash expression string.
    """
    if dialect == "duckdb":
        parts = [f"""COALESCE(CAST("{col}" AS VARCHAR), '')""" for col in columns]
    else:
        parts = [f"""COALESCE("{col}", '')""" for col in columns]
    concat = " || '||' || ".join(parts)
    # Lookup: dialect+algo -> default+algo -> default+sha256
    dialect_funcs = _HASH_FUNCTIONS.get(dialect, _HASH_FUNCTIONS["default"])
    template = dialect_funcs.get(
        hash_algo,
        _HASH_FUNCTIONS["default"].get(hash_algo, _HASH_FUNCTIONS["default"]["sha256"]),
    )
    return template.format(expr=concat)
