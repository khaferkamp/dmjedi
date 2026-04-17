"""End-to-end integration tests for the DMJEDI pipeline."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from dmjedi.docs.markdown import generate_markdown
from dmjedi.generators import registry
from dmjedi.lang.imports import resolve_imports
from dmjedi.lang.linter import Severity, lint
from dmjedi.lang.parser import parse, parse_file
from dmjedi.model.core import Column, DataVaultModel, Hub, Link, Satellite
from dmjedi.model.resolver import ResolverErrors, resolve
from tests.fixtures.all_entity_rows import (
    CUSTOMER_MATCH_1001_HK,
    CUSTOMER_1001_HK,
    CUSTOMER_1002_HK,
    CUSTOMER_PRODUCT_1001_2001_HK,
    CUSTOMER_PRODUCT_1002_2002_HK,
    PRODUCT_2001_HK,
    PRODUCT_2002_HK,
)
from tests.helpers.sql_execution import execute_sql_files, fetch_all, load_source_tables


def _sample_model() -> DataVaultModel:
    return DataVaultModel(
        hubs={
            "sales.Customer": Hub(
                name="Customer",
                namespace="sales",
                business_keys=[
                    Column(name="customer_id", data_type="int", is_business_key=True)
                ],
            )
        },
        satellites={
            "sales.CustomerDetails": Satellite(
                name="CustomerDetails",
                namespace="sales",
                parent_ref="Customer",
                columns=[Column(name="first_name", data_type="string")],
            )
        },
        links={
            "sales.CustomerProduct": Link(
                name="CustomerProduct",
                namespace="sales",
                hub_references=["Customer", "Product"],
            )
        },
    )


# ---------------------------------------------------------------------------
# E2E pipeline tests
# ---------------------------------------------------------------------------


def test_e2e_sql_pipeline():
    """Full pipeline: .dv file -> parse -> lint -> resolve -> SQL generation."""
    module = parse_file(Path("examples/sales-domain.dv"))

    diagnostics = lint(module)
    errors = [d for d in diagnostics if d.severity == Severity.ERROR]
    assert not errors, f"Unexpected lint errors: {errors}"

    model = resolve([module])

    gen = registry.get("sql-jinja")
    result = gen.generate(model)

    ddl_files = {k: v for k, v in result.files.items() if not k.startswith("staging/")}
    assert len(ddl_files) == 8, f"Expected 8 DDL files, got {sorted(ddl_files.keys())}"

    for filename, sql in ddl_files.items():
        assert "CREATE TABLE" in sql, f"{filename} missing CREATE TABLE"
        stripped = sql.replace(" ", "").replace("\n", "")
        assert ",)" not in stripped, f"{filename} has trailing comma before )"

    staging_files = {k: v for k, v in result.files.items() if k.startswith("staging/")}
    assert len(staging_files) == 8, f"Expected 8 staging files, got {sorted(staging_files.keys())}"
    for filename, sql in staging_files.items():
        assert "CREATE OR REPLACE VIEW" in sql, f"{filename} missing CREATE OR REPLACE VIEW"


def test_e2e_spark_pipeline():
    """Full pipeline: .dv file -> parse -> resolve -> Spark DLT generation."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    gen = registry.get("spark-declarative")
    result = gen.generate(model)

    assert len(result.files) == 8, f"Expected 8 files, got {sorted(result.files.keys())}"

    for filename, code in result.files.items():
        assert "import dlt" in code, f"{filename} missing 'import dlt'"
        assert "@dlt.table" in code, f"{filename} missing '@dlt.table'"
        lines = [ln.strip() for ln in code.splitlines()]
        assert "pass" not in lines, f"{filename} contains 'pass' stub"
        assert not any("TODO" in ln for ln in lines), f"{filename} contains TODO"
        compile(code, filename, "exec")


def test_e2e_docs_pipeline():
    """Full pipeline: .dv file -> parse -> resolve -> markdown documentation."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    md = generate_markdown(model)

    assert "# Data Vault Model Documentation" in md
    for name in ("Customer", "Product", "Store", "Sale"):
        assert name in md, f"Entity '{name}' not found in docs output"


def test_e2e_multifile_resolve():
    """Multi-file pipeline: parse main.dv -> resolve imports -> resolve model."""
    module = parse_file(Path("tests/fixtures/imports/main.dv"))

    modules = resolve_imports([module])
    assert len(modules) >= 2, "Expected at least 2 modules after import resolution"

    model = resolve(modules)

    assert any("Customer" in k for k in model.hubs), "Hub from hub_defs.dv not resolved"
    assert any("CustomerDetails" in k for k in model.satellites), (
        "Satellite from main.dv not resolved"
    )


def test_e2e_validation_errors():
    """Error pipeline: parse bad DVML -> lint -> expect ERROR diagnostics."""
    module = parse("namespace t\nhub Bad {}")

    diagnostics = lint(module)

    error_diags = [d for d in diagnostics if d.severity == Severity.ERROR]
    assert error_diags, "Expected at least one ERROR diagnostic"
    assert any(d.rule == "hub-requires-business-key" for d in error_diags)


def test_e2e_resolver_errors():
    """Error pipeline: duplicate entities -> ResolverErrors raised."""
    mod1 = parse("namespace dup\nhub Same {\n  business_key id : int\n}", source_file="a.dv")
    mod2 = parse("namespace dup\nhub Same {\n  business_key id : int\n}", source_file="b.dv")

    with pytest.raises(ResolverErrors, match="Duplicate"):
        resolve([mod1, mod2])


def test_e2e_write_to_disk(tmp_path: Path):
    """Verify GeneratorResult.write() creates files on disk."""
    module = parse_file(Path("examples/sales-domain.dv"))
    model = resolve([module])

    gen = registry.get("sql-jinja")
    result = gen.generate(model)

    written = result.write(tmp_path)
    assert len(written) == len(result.files)

    for path in written:
        assert path.exists(), f"Written file does not exist: {path}"

    # Verify at least one file's content matches
    first_rel = next(iter(result.files))
    first_path = tmp_path / first_rel
    assert first_path.read_text() == result.files[first_rel]


def test_e2e_duckdb_behavioral_sql_flow(duckdb_generated_result, all_entity_source_rows):
    """Generated DuckDB SQL should produce observable rows from canonical source data."""
    conn = duckdb.connect(":memory:")
    try:
        load_source_tables(conn, all_entity_source_rows)
        _create_non_historized_targets(conn)
        _execute_all_generated_duckdb_files(conn, duckdb_generated_result.files)
        _load_historized_targets(conn)

        customer_rows = fetch_all(
            conn,
            'SELECT "Customer_hk", "customer_id" FROM "Customer" ORDER BY "customer_id"',
        )
        assert customer_rows == [
            (CUSTOMER_1001_HK, 1001),
            (CUSTOMER_1002_HK, 1002),
        ]

        satellite_rows = fetch_all(
            conn,
            'SELECT "Customer_hk", "first_name", "last_name", "email" '
            'FROM "CustomerDetails" ORDER BY "email"',
        )
        assert satellite_rows == [
            (CUSTOMER_1001_HK, "Ana", "Nguyen", "ana.nguyen@example.com"),
            (CUSTOMER_1002_HK, "Ben", "Patel", "ben.patel@example.com"),
        ]

        link_rows = fetch_all(
            conn,
            'SELECT "CustomerProduct_hk", "Customer_hk", "Product_hk", "quantity" '
            'FROM "CustomerProduct" ORDER BY "quantity" DESC, "CustomerProduct_hk"',
        )
        assert link_rows == [
            (CUSTOMER_PRODUCT_1001_2001_HK, CUSTOMER_1001_HK, PRODUCT_2001_HK, 2),
            (CUSTOMER_PRODUCT_1002_2002_HK, CUSTOMER_1002_HK, PRODUCT_2002_HK, 1),
        ]

        nhsat_rows = fetch_all(
            conn,
            'SELECT "Customer_hk", "status", "updated_at" '
            'FROM "CurrentStatus" ORDER BY "status"',
        )
        assert nhsat_rows == [
            (CUSTOMER_1001_HK, "active", datetime(2026, 1, 5, 9, 30, 0)),
            (CUSTOMER_1002_HK, "trial", datetime(2026, 1, 6, 14, 45, 0)),
        ]

        nhlink_rows = fetch_all(
            conn,
            'SELECT "ActiveRelation_hk", "Customer_hk", "Product_hk", "score" '
            'FROM "ActiveRelation" ORDER BY "score" DESC',
        )
        assert nhlink_rows == [
            (
                CUSTOMER_PRODUCT_1001_2001_HK,
                CUSTOMER_1001_HK,
                PRODUCT_2001_HK,
                Decimal("0.980000"),
            ),
            (
                CUSTOMER_PRODUCT_1002_2002_HK,
                CUSTOMER_1002_HK,
                PRODUCT_2002_HK,
                Decimal("0.870000"),
            ),
        ]

        effsat_rows = fetch_all(
            conn,
            'SELECT "CustomerProduct_hk", "valid_from", "valid_to" '
            'FROM "RelationValidity" ORDER BY "valid_from"',
        )
        assert effsat_rows == [
            (
                CUSTOMER_PRODUCT_1001_2001_HK,
                datetime(2026, 1, 5, 0, 0, 0),
                datetime(2026, 12, 31, 23, 59, 59),
            ),
            (
                CUSTOMER_PRODUCT_1002_2002_HK,
                datetime(2026, 1, 6, 0, 0, 0),
                datetime(2026, 12, 31, 23, 59, 59),
            ),
        ]

        samlink_rows = fetch_all(
            conn,
            'SELECT "CustomerMatch_hk", "master_Customer_hk", "duplicate_Customer_hk", "confidence" '
            'FROM "CustomerMatch"',
        )
        assert samlink_rows == [
            (
                CUSTOMER_MATCH_1001_HK,
                CUSTOMER_1001_HK,
                CUSTOMER_1001_HK,
                Decimal("0.910000"),
            )
        ]

        bridge_rows = fetch_all(
            conn,
            'SELECT "Customer_hk", "CustomerProduct_hk", "Product_hk" '
            'FROM "bridge_CustomerProductBridge" ORDER BY "CustomerProduct_hk"',
        )
        assert bridge_rows == [
            (CUSTOMER_1002_HK, CUSTOMER_PRODUCT_1002_2002_HK, PRODUCT_2002_HK),
            (CUSTOMER_1001_HK, CUSTOMER_PRODUCT_1001_2001_HK, PRODUCT_2001_HK),
        ]

        pit_rows = fetch_all(
            conn,
            'SELECT "Customer_hk", "CustomerDetails_hash_diff" '
            'FROM "pit_CustomerPit" ORDER BY "Customer_hk"',
        )
        assert len(pit_rows) == 2
        assert all(customer_hk in {CUSTOMER_1001_HK, CUSTOMER_1002_HK} for customer_hk, _ in pit_rows)
        assert all(isinstance(hash_diff, str) and len(hash_diff) == 64 for _, hash_diff in pit_rows)
    finally:
        conn.close()


def test_e2e_duckdb_executes_every_generated_sql_file(
    duckdb_generated_result,
    all_entity_source_rows,
):
    """The canonical DuckDB fixture should execute the full generated SQL file map."""
    conn = duckdb.connect(":memory:")
    try:
        load_source_tables(conn, all_entity_source_rows)
        _create_non_historized_targets(conn)
        _execute_all_generated_duckdb_files(conn, duckdb_generated_result.files)
        _load_historized_targets(conn)
    finally:
        conn.close()


def _create_non_historized_targets(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        'CREATE TABLE "CurrentStatus" ('
        '"Customer_hk" CHAR(64), '
        '"load_ts" TIMESTAMP, '
        '"record_source" VARCHAR, '
        '"status" VARCHAR, '
        '"updated_at" TIMESTAMP)'
    )
    conn.execute(
        'CREATE TABLE "ActiveRelation" ('
        '"ActiveRelation_hk" CHAR(64), '
        '"load_ts" TIMESTAMP, '
        '"record_source" VARCHAR, '
        '"Customer_hk" CHAR(64), '
        '"Product_hk" CHAR(64), '
        '"score" DECIMAL(18,6))'
    )
    conn.execute(
        'CREATE TABLE "RelationValidity" ('
        '"CustomerProduct_hk" CHAR(64), '
        '"load_ts" TIMESTAMP, '
        '"record_source" VARCHAR, '
        '"valid_from" TIMESTAMP, '
        '"valid_to" TIMESTAMP)'
    )
    conn.execute(
        'CREATE TABLE "CustomerMatch" ('
        '"CustomerMatch_hk" CHAR(64), '
        '"load_ts" TIMESTAMP, '
        '"record_source" VARCHAR, '
        '"master_Customer_hk" CHAR(64), '
        '"duplicate_Customer_hk" CHAR(64), '
        '"confidence" DECIMAL(18,6))'
    )


def _execute_all_generated_duckdb_files(
    conn: duckdb.DuckDBPyConnection,
    files: dict[str, str],
) -> None:
    staging_prefixes = ("staging/hubs/", "staging/satellites/", "staging/links/")
    raw_prefixes = ("hubs/", "satellites/", "links/")
    view_prefixes = ("views/",)

    executed_paths = {
        path
        for prefixes in (staging_prefixes, raw_prefixes, view_prefixes)
        for path in files
        if any(path.startswith(prefix) for prefix in prefixes)
    }
    assert executed_paths == set(files)

    execute_sql_files(conn, files, prefixes=staging_prefixes)
    execute_sql_files(conn, files, prefixes=raw_prefixes)
    execute_sql_files(conn, files, prefixes=view_prefixes)


def _load_historized_targets(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute('INSERT INTO "Customer" SELECT * FROM "stg_Customer"')
    conn.execute('INSERT INTO "Product" SELECT * FROM "stg_Product"')
    conn.execute('INSERT INTO "CustomerDetails" SELECT * FROM "stg_CustomerDetails"')
    conn.execute('INSERT INTO "CustomerProduct" SELECT * FROM "stg_CustomerProduct"')


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


def test_sql_hub_snapshot(snapshot):
    """Snapshot test for hub SQL output."""
    model = _sample_model()
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    snapshot.assert_match(result.files["hubs/Customer.sql"], "hub_customer.sql")


def test_sql_link_snapshot(snapshot):
    """Snapshot test for link SQL output."""
    model = _sample_model()
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    snapshot.assert_match(result.files["links/CustomerProduct.sql"], "link_customerproduct.sql")


def test_spark_hub_snapshot(snapshot):
    """Snapshot test for hub Spark output."""
    model = _sample_model()
    gen = registry.get("spark-declarative")
    result = gen.generate(model)
    snapshot.assert_match(result.files["hubs/Customer.py"], "hub_customer.py")
