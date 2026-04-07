"""Tests for the generator registry and built-in generators."""

from dmjedi.generators import registry
from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator
from dmjedi.generators.sql_jinja.types import map_type
from dmjedi.model.core import Column, DataVaultModel, Hub, Link, Satellite


def _sample_model() -> DataVaultModel:
    return DataVaultModel(
        hubs={
            "sales.Customer": Hub(
                name="Customer",
                namespace="sales",
                business_keys=[Column(name="customer_id", data_type="int", is_business_key=True)],
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


def _assert_valid_sql(sql: str) -> None:
    """Basic SQL validation: balanced parens, no trailing commas, no double commas."""
    assert sql.count("(") == sql.count(")"), f"Unbalanced parentheses:\n{sql}"
    stripped = sql.replace(" ", "").replace("\n", "")
    assert ",)" not in stripped, f"Trailing comma before ):\n{sql}"
    assert ",," not in stripped, f"Double comma:\n{sql}"


def test_registry_has_builtins():
    names = registry.available()
    assert "spark-declarative" in names
    assert "sql-jinja" in names


def test_spark_declarative_generates_files():
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model())
    assert "hubs/Customer.py" in result.files
    assert "satellites/CustomerDetails.py" in result.files
    assert "links/CustomerProduct.py" in result.files


def test_sql_jinja_generates_files():
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model())
    assert "hubs/Customer.sql" in result.files
    assert "CREATE TABLE" in result.files["hubs/Customer.sql"]


def test_unknown_generator_raises():
    import pytest

    with pytest.raises(KeyError, match="Unknown generator"):
        registry.get("nonexistent")


# --- SQL validation tests ---


def test_sql_hub_output_valid():
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model())
    sql = result.files["hubs/Customer.sql"]
    _assert_valid_sql(sql)
    assert "CREATE TABLE IF NOT EXISTS Customer" in sql
    assert "Customer_hk BINARY NOT NULL" in sql
    assert "load_ts TIMESTAMP NOT NULL" in sql
    assert "record_source" in sql
    assert "customer_id INT" in sql


def test_sql_satellite_output_valid():
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model())
    sql = result.files["satellites/CustomerDetails.sql"]
    _assert_valid_sql(sql)
    assert "CREATE TABLE IF NOT EXISTS CustomerDetails" in sql
    assert "Customer_hk BINARY NOT NULL" in sql
    assert "hash_diff BINARY NOT NULL" in sql
    assert "load_end_ts TIMESTAMP" in sql
    assert "first_name VARCHAR(255)" in sql


def test_sql_link_no_columns_valid():
    """Link with NO extra columns -- the trailing-comma bug case."""
    model = DataVaultModel(
        hubs={},
        satellites={},
        links={
            "s.AB": Link(name="AB", namespace="s", hub_references=["A", "B"]),
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    sql = result.files["links/AB.sql"]
    _assert_valid_sql(sql)
    assert "A_hk BINARY NOT NULL" in sql
    assert "B_hk BINARY NOT NULL" in sql


def test_sql_link_with_columns_valid():
    """Link WITH extra columns -- hub refs and columns both present."""
    model = DataVaultModel(
        hubs={},
        satellites={},
        links={
            "s.AB": Link(
                name="AB",
                namespace="s",
                hub_references=["A", "B"],
                columns=[Column(name="amount", data_type="decimal")],
            ),
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    sql = result.files["links/AB.sql"]
    _assert_valid_sql(sql)
    assert "A_hk BINARY NOT NULL" in sql
    assert "B_hk BINARY NOT NULL" in sql
    assert "amount DECIMAL(18,2)" in sql


def test_sql_satellite_no_columns_valid():
    """Satellite with NO user columns -- hash_diff should not have trailing comma."""
    model = DataVaultModel(
        hubs={},
        satellites={
            "s.EmptySat": Satellite(
                name="EmptySat", namespace="s", parent_ref="Parent", columns=[]
            ),
        },
        links={},
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    sql = result.files["satellites/EmptySat.sql"]
    _assert_valid_sql(sql)
    assert "hash_diff BINARY NOT NULL" in sql


def test_sql_type_mapping_default():
    assert map_type("string") == "VARCHAR(255)"
    assert map_type("int") == "INT"
    assert map_type("decimal") == "DECIMAL(18,2)"
    assert map_type("date") == "DATE"
    assert map_type("timestamp") == "TIMESTAMP"
    assert map_type("boolean") == "BOOLEAN"
    assert map_type("json") == "JSON"


def test_sql_type_mapping_postgres():
    assert map_type("string", "postgres") == "TEXT"
    assert map_type("int", "postgres") == "INTEGER"
    assert map_type("decimal", "postgres") == "NUMERIC(18,2)"
    assert map_type("json", "postgres") == "JSONB"


def test_sql_type_mapping_spark():
    assert map_type("string", "spark") == "STRING"
    assert map_type("int", "spark") == "INT"
    assert map_type("json", "spark") == "STRING"


def test_sql_type_mapping_unknown_passthrough():
    """Unknown DVML types are passed through uppercased."""
    assert map_type("binary") == "BINARY"
    assert map_type("CustomType") == "CUSTOMTYPE"


def test_sql_jinja_postgres_dialect():
    """Verify dialect parameter flows through to templates."""
    gen = SqlJinjaGenerator(dialect="postgres")
    model = _sample_model()
    result = gen.generate(model)
    hub_sql = result.files["hubs/Customer.sql"]
    assert "TEXT" in hub_sql  # record_source mapped to TEXT for postgres
    sat_sql = result.files["satellites/CustomerDetails.sql"]
    assert "TEXT" in sat_sql  # first_name mapped to TEXT for postgres
