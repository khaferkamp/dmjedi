"""DuckDB execution helpers for generated SQL integration tests."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, TypeAlias

SqlScalar: TypeAlias = str | int | float | bool | Decimal | datetime | date | None
SourceRow: TypeAlias = dict[str, SqlScalar]
SourceRows: TypeAlias = dict[str, list[SourceRow]]


class SqlExecutor(Protocol):
    def execute(self, sql: str, parameters: Sequence[SqlScalar] | None = None) -> object: ...


_EXECUTION_GROUPS: tuple[tuple[str, ...], ...] = (
    ("hubs/",),
    ("satellites/",),
    ("links/",),
    ("staging/hubs/",),
    ("staging/satellites/",),
    ("staging/links/",),
    ("views/bridge_",),
    ("views/pit_",),
)


def execute_sql_files(
    conn: SqlExecutor,
    files: dict[str, str],
    *,
    prefixes: tuple[str, ...],
) -> None:
    """Execute selected SQL files in dependency-safe order."""
    filtered_paths = [
        path for path in files if any(path.startswith(prefix) for prefix in prefixes)
    ]

    for path in sorted(filtered_paths, key=_execution_sort_key):
        conn.execute(files[path])


def load_source_tables(conn: SqlExecutor, source_rows: SourceRows) -> None:
    """Create `src_*` tables and load canonical rows into DuckDB."""
    for table_name, rows in sorted(source_rows.items()):
        columns = _collect_columns(rows)
        ddl = ", ".join(
            f'{_quote_identifier(column)} {_duckdb_type_for(rows, column)}'
            for column in columns
        )
        conn.execute(f'CREATE TABLE {_quote_identifier(table_name)} ({ddl})')

        if not rows:
            continue

        placeholders = ", ".join("?" for _ in columns)
        insert_sql = (
            f'INSERT INTO {_quote_identifier(table_name)} '
            f'VALUES ({placeholders})'
        )
        for row in rows:
            parameters = tuple(row.get(column) for column in columns)
            conn.execute(insert_sql, parameters)


def fetch_all(conn: SqlExecutor, sql: str) -> list[tuple[object, ...]]:
    """Run a query and return all rows."""
    result = conn.execute(sql)
    return result.fetchall()


def _execution_sort_key(path: str) -> tuple[int, str]:
    for index, prefixes in enumerate(_EXECUTION_GROUPS):
        if any(path.startswith(prefix) for prefix in prefixes):
            return (index, path)
    return (len(_EXECUTION_GROUPS), path)


def _collect_columns(rows: Iterable[SourceRow]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _duckdb_type_for(rows: Sequence[SourceRow], column: str) -> str:
    for row in rows:
        value = row.get(column)
        if value is None:
            continue
        if isinstance(value, bool):
            return "BOOLEAN"
        if isinstance(value, int):
            return "BIGINT"
        if isinstance(value, float):
            return "DOUBLE"
        if isinstance(value, Decimal):
            return "DECIMAL(18,6)"
        if isinstance(value, datetime):
            return "TIMESTAMP"
        if isinstance(value, date):
            return "DATE"
        return "VARCHAR"
    return "VARCHAR"


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier}"'
