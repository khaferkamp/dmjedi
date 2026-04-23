"""Tests for shared SQL execution helpers and canonical fixture data."""

import duckdb

EXPECTED_SOURCE_TABLES = {
    "src_Customer",
    "src_Product",
    "src_CustomerDetails",
    "src_CustomerProduct",
    "src_CurrentStatus",
    "src_ActiveRelation",
    "src_RelationValidity",
    "src_CustomerMatch",
}


def test_canonical_source_rows_cover_expected_tables(
    all_entity_source_rows: dict[str, list[dict[str, object]]],
) -> None:
    """Canonical source data should cover every generated staging input table."""
    assert set(all_entity_source_rows) == EXPECTED_SOURCE_TABLES


class RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, sql: str) -> None:
        self.statements.append(sql)


def test_execute_sql_files_orders_selected_files_for_execution() -> None:
    """Execution order should respect DDL, staging, and downstream view dependencies."""
    from tests.helpers.sql_execution import execute_sql_files

    files = {
        "views/pit_CustomerPit.sql": "pit-sql",
        "staging/links/CustomerProduct.sql": "staging-link-sql",
        "links/CustomerProduct.sql": "link-ddl-sql",
        "hubs/Customer.sql": "hub-ddl-sql",
        "staging/hubs/Customer.sql": "staging-hub-sql",
        "views/bridge_CustomerProductBridge.sql": "bridge-sql",
        "satellites/CustomerDetails.sql": "satellite-ddl-sql",
    }

    conn = RecordingConnection()

    execute_sql_files(
        conn,
        files,
        prefixes=("views/", "staging/", "links/", "hubs/", "satellites/"),
    )

    assert conn.statements == [
        "hub-ddl-sql",
        "satellite-ddl-sql",
        "link-ddl-sql",
        "staging-hub-sql",
        "staging-link-sql",
        "bridge-sql",
        "pit-sql",
    ]


def test_execute_sql_files_filters_real_generator_layout(duckdb_generated_result) -> None:
    """Prefix filtering should follow the generator's live file layout."""
    from tests.helpers.sql_execution import execute_sql_files

    conn = RecordingConnection()

    execute_sql_files(
        conn,
        duckdb_generated_result.files,
        prefixes=("views/", "staging/hubs/"),
    )

    assert conn.statements == [
        duckdb_generated_result.files["staging/hubs/Customer.sql"],
        duckdb_generated_result.files["staging/hubs/Product.sql"],
        duckdb_generated_result.files["views/bridge_CustomerProductBridge.sql"],
        duckdb_generated_result.files["views/pit_CustomerPit.sql"],
    ]


def test_load_source_tables_creates_src_tables_and_rows(
    all_entity_source_rows: dict[str, list[dict[str, object]]],
) -> None:
    """Source row helper should create tables and load the canonical payloads."""
    from tests.helpers.sql_execution import fetch_all, load_source_tables

    conn = duckdb.connect(":memory:")
    try:
        load_source_tables(conn, all_entity_source_rows)

        assert fetch_all(
            conn,
            'SELECT "customer_id" FROM "src_Customer" ORDER BY "customer_id"',
        ) == [(1001,), (1002,)]
        assert fetch_all(
            conn,
            'SELECT "sku" FROM "src_Product" ORDER BY "product_id"',
        ) == [("SKU-001",), ("SKU-002",)]
    finally:
        conn.close()
