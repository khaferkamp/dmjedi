"""Tests for the generator registry and built-in generators."""

from dmjedi.generators import registry
from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator
from dmjedi.generators.sql_jinja.types import map_type
from dmjedi.model.core import (
    Bridge,
    Column,
    DataVaultModel,
    EffSat,
    Hub,
    Link,
    NhLink,
    NhSat,
    Pit,
    SamLink,
    Satellite,
)


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
    assert map_type("blob") == "BLOB"
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


# --- Spark DLT functional tests ---


def test_spark_hub_output_functional():
    """Hub generates functional DLT code with hash key, load_ts, record_source, distinct."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model())
    code = result.files["hubs/Customer.py"]
    assert "import dlt" in code
    assert "@dlt.table(" in code
    assert 'name="hub_Customer"' in code
    assert 'F.sha2(F.concat_ws("||"' in code
    assert 'F.current_timestamp().alias("load_ts")' in code
    assert 'F.lit("dmjedi").alias("record_source")' in code
    assert ".distinct()" in code
    assert "customer_id" in code
    # No stubs
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines
    assert not any("TODO" in ln for ln in lines)


def test_spark_satellite_output_functional():
    """Satellite generates DLT code with parent hk, hash_diff, user columns."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model())
    code = result.files["satellites/CustomerDetails.py"]
    assert 'name="sat_CustomerDetails"' in code
    assert "Customer_hk" in code
    assert "hash_diff" in code
    assert "first_name" in code
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines
    assert not any("TODO" in ln for ln in lines)


def test_spark_link_output_functional():
    """Link generates DLT code with composite hash key from hub ref hks."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model())
    code = result.files["links/CustomerProduct.py"]
    assert 'name="link_CustomerProduct"' in code
    assert "Customer_hk" in code
    assert "Product_hk" in code
    assert 'F.sha2(F.concat_ws("||"' in code
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines
    assert not any("TODO" in ln for ln in lines)


def test_spark_link_no_extra_columns():
    """Link with no extra columns still produces valid DLT output."""
    model = DataVaultModel(
        hubs={},
        satellites={},
        links={
            "s.AB": Link(name="AB", namespace="s", hub_references=["A", "B"]),
        },
    )
    gen = registry.get("spark-declarative")
    result = gen.generate(model)
    code = result.files["links/AB.py"]
    assert 'name="link_AB"' in code
    assert "A_hk" in code
    assert "B_hk" in code
    assert "import dlt" in code
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines


def test_spark_satellite_column_type_mapping():
    """Verify Spark generator uses map_pyspark_type for column types (end-to-end)."""
    model = DataVaultModel(
        hubs={"ns.TestHub": Hub(name="TestHub", namespace="ns", business_keys=[Column(name="id", data_type="int")])},
        satellites={"ns.TestSat": Satellite(
            name="TestSat", namespace="ns", parent_ref="TestHub",
            columns=[Column(name="amount", data_type="bigint")]
        )},
        links={},
    )
    gen = registry.get("spark-declarative")
    result = gen.generate(model)
    sat_code = result.files["satellites/TestSat.py"]
    assert "LongType()" in sat_code, "bigint column should map to LongType() in Spark output"
    assert ".cast(" in sat_code, "typed columns should use .cast() in Spark output"


# --- Non-historized entity helpers ---


def _sample_model_with_nh() -> DataVaultModel:
    """DataVaultModel including nhsat and nhlink entities for generator tests."""
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
        nhsats={
            "sales.CurrentStatus": NhSat(
                name="CurrentStatus",
                namespace="sales",
                parent_ref="Customer",
                columns=[Column(name="status", data_type="string")],
            )
        },
        nhlinks={
            "sales.AB": NhLink(
                name="AB",
                namespace="sales",
                hub_references=["A", "B"],
                columns=[Column(name="amount", data_type="decimal")],
            )
        },
    )


# --- SQL Jinja non-historized tests ---


def test_sql_nhsat_output_valid():
    """NhSat SQL uses MERGE INTO, includes parent hk, no historized fields, passes SQL validation."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_nh())
    assert "satellites/nhsat_CurrentStatus.sql" in result.files
    sql = result.files["satellites/nhsat_CurrentStatus.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql
    assert "Customer_hk" in sql
    assert "hash_diff" not in sql
    assert "load_end_ts" not in sql
    assert "status" in sql


def test_sql_nhlink_output_valid():
    """NhLink SQL uses MERGE INTO, includes link hk and hub ref hks, passes SQL validation."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_nh())
    assert "links/nhlink_AB.sql" in result.files
    sql = result.files["links/nhlink_AB.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql
    assert "AB_hk" in sql
    assert "A_hk" in sql
    assert "B_hk" in sql
    assert "amount" in sql


def test_sql_nhsat_no_columns_valid():
    """NhSat with no user columns: no trailing comma bug."""
    model = DataVaultModel(
        nhsats={
            "s.EmptyNhSat": NhSat(
                name="EmptyNhSat", namespace="s", parent_ref="Parent", columns=[]
            )
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    assert "satellites/nhsat_EmptyNhSat.sql" in result.files
    sql = result.files["satellites/nhsat_EmptyNhSat.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql


def test_sql_nhlink_no_columns_valid():
    """NhLink with no extra columns: no trailing comma bug."""
    model = DataVaultModel(
        nhlinks={
            "s.XY": NhLink(name="XY", namespace="s", hub_references=["X", "Y"], columns=[])
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    assert "links/nhlink_XY.sql" in result.files
    sql = result.files["links/nhlink_XY.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql


# --- Spark DLT non-historized tests ---


def test_spark_nhsat_output_functional():
    """NhSat Spark code uses dlt.apply_changes with stored_as_scd_type=1, no historized fields."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_nh())
    assert "satellites/nhsat_CurrentStatus.py" in result.files
    code = result.files["satellites/nhsat_CurrentStatus.py"]
    assert "import dlt" in code
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code
    assert "Customer_hk" in code
    assert "hash_diff" not in code
    assert "nhsat_CurrentStatus" in code
    # apply_changes infers schema at runtime — column names must NOT appear
    assert "status" not in code


def test_spark_nhlink_output_functional():
    """NhLink Spark code uses dlt.apply_changes with stored_as_scd_type=1."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_nh())
    assert "links/nhlink_AB.py" in result.files
    code = result.files["links/nhlink_AB.py"]
    assert "import dlt" in code
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code
    assert "AB_hk" in code
    assert "nhlink_AB" in code
    # apply_changes infers schema at runtime — column names must NOT appear
    assert "amount" not in code


def test_spark_nhsat_no_columns():
    """NhSat with empty columns still generates valid apply_changes code."""
    model = DataVaultModel(
        nhsats={
            "s.EmptyNhSat": NhSat(
                name="EmptyNhSat", namespace="s", parent_ref="Parent", columns=[]
            )
        },
    )
    gen = registry.get("spark-declarative")
    result = gen.generate(model)
    assert "satellites/nhsat_EmptyNhSat.py" in result.files
    code = result.files["satellites/nhsat_EmptyNhSat.py"]
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code


# --- Bridge/PIT helper ---


def _sample_model_with_bridge_pit() -> DataVaultModel:
    """DataVaultModel including bridge and pit entities for generator tests."""
    return DataVaultModel(
        hubs={
            "sales.Customer": Hub(
                name="Customer",
                namespace="sales",
                business_keys=[Column(name="customer_id", data_type="int", is_business_key=True)],
            ),
            "sales.Product": Hub(
                name="Product",
                namespace="sales",
                business_keys=[Column(name="product_id", data_type="int", is_business_key=True)],
            ),
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
        bridges={
            "sales.CustProd": Bridge(
                name="CustProd",
                namespace="sales",
                path=["Customer", "CustomerProduct", "Product"],
            )
        },
        pits={
            "sales.CustPit": Pit(
                name="CustPit",
                namespace="sales",
                anchor_ref="Customer",
                tracked_satellites=["CustomerDetails"],
            )
        },
    )


# --- SQL Jinja bridge/PIT tests ---


def test_sql_bridge_output_valid():
    """Bridge SQL generates a CREATE OR REPLACE VIEW with JOIN chain, not a table."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_bridge_pit())
    assert "views/bridge_CustProd.sql" in result.files
    sql = result.files["views/bridge_CustProd.sql"]
    _assert_valid_sql(sql)
    assert "CREATE OR REPLACE VIEW" in sql
    assert "CREATE TABLE" not in sql
    assert "bridge_CustProd" in sql
    assert "Customer" in sql
    assert "CustomerProduct" in sql
    assert "Product" in sql
    assert "JOIN" in sql


def test_sql_pit_output_valid():
    """PIT SQL generates a CREATE OR REPLACE VIEW with LEFT JOINs for tracked satellites."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_bridge_pit())
    assert "views/pit_CustPit.sql" in result.files
    sql = result.files["views/pit_CustPit.sql"]
    _assert_valid_sql(sql)
    assert "CREATE OR REPLACE VIEW" in sql
    assert "CREATE TABLE" not in sql
    assert "pit_CustPit" in sql
    assert "Customer_hk" in sql
    assert "LEFT JOIN" in sql
    assert "CustomerDetails" in sql


def test_sql_bridge_no_create_table():
    """Generating a model with only a bridge produces no file with CREATE TABLE and bridge in name."""
    model = DataVaultModel(
        bridges={
            "s.MyBridge": Bridge(
                name="MyBridge",
                namespace="s",
                path=["HubA", "LinkAB", "HubB"],
            )
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    for filename, content in result.files.items():
        if "bridge" in filename.lower():
            assert "CREATE TABLE" not in content, f"Expected no CREATE TABLE in {filename}"


def test_sql_pit_no_create_table():
    """Generating a model with only a pit produces no file with CREATE TABLE and pit in name."""
    model = DataVaultModel(
        pits={
            "s.MyPit": Pit(
                name="MyPit",
                namespace="s",
                anchor_ref="SomeHub",
                tracked_satellites=[],
            )
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    for filename, content in result.files.items():
        if "pit" in filename.lower():
            assert "CREATE TABLE" not in content, f"Expected no CREATE TABLE in {filename}"


# --- Spark DLT bridge/PIT tests ---


def test_spark_bridge_output_functional():
    """Bridge Spark code uses @dlt.view, dlt.read calls, and .join() — no @dlt.table."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_bridge_pit())
    assert "views/bridge_CustProd.py" in result.files
    code = result.files["views/bridge_CustProd.py"]
    assert "import dlt" in code
    assert "@dlt.view(" in code
    assert "@dlt.table" not in code
    assert "bridge_CustProd" in code
    assert "dlt.read" in code
    assert ".join(" in code
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines
    assert not any("TODO" in ln for ln in lines)


def test_spark_pit_output_functional():
    """PIT Spark code uses @dlt.view, Window/row_number, left join — no @dlt.table."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_bridge_pit())
    assert "views/pit_CustPit.py" in result.files
    code = result.files["views/pit_CustPit.py"]
    assert "import dlt" in code
    assert "@dlt.view(" in code
    assert "@dlt.table" not in code
    assert "pit_CustPit" in code
    assert "dlt.read" in code
    assert "Window" in code
    assert "row_number" in code
    assert ".join(" in code
    assert '"left"' in code
    lines = [ln.strip() for ln in code.splitlines()]
    assert "pass" not in lines
    assert not any("TODO" in ln for ln in lines)


def test_spark_bridge_no_dlt_table():
    """Bridge Spark code never uses @dlt.table decorator."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_bridge_pit())
    code = result.files["views/bridge_CustProd.py"]
    assert "@dlt.table" not in code


def test_spark_pit_no_dlt_table():
    """PIT Spark code never uses @dlt.table decorator."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_bridge_pit())
    code = result.files["views/pit_CustPit.py"]
    assert "@dlt.table" not in code


# --- EffSat / SamLink helper ---


def _sample_model_with_effsat_samlink() -> DataVaultModel:
    """DataVaultModel including EffSat and SamLink entities for generator tests."""
    return DataVaultModel(
        effsats={
            "sales.CustProdValidity": EffSat(
                name="CustProdValidity",
                namespace="sales",
                parent_ref="CustomerProduct",
                columns=[
                    Column(name="valid_from", data_type="timestamp"),
                    Column(name="valid_to", data_type="timestamp"),
                ],
            )
        },
        samlinks={
            "sales.CustomerMatch": SamLink(
                name="CustomerMatch",
                namespace="sales",
                master_ref="Customer",
                duplicate_ref="Customer",
                columns=[Column(name="confidence", data_type="decimal")],
            )
        },
    )


# --- SQL Jinja EffSat tests ---


def test_sql_effsat_output_valid():
    """EffSat SQL uses MERGE INTO, parent_ref_hk as key, columns rendered, no historized fields."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_effsat_samlink())
    assert "satellites/effsat_CustProdValidity.sql" in result.files
    sql = result.files["satellites/effsat_CustProdValidity.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql
    assert "CustomerProduct_hk" in sql
    assert "valid_from" in sql
    assert "valid_to" in sql
    assert "hash_diff" not in sql
    assert "load_end_ts" not in sql


def test_sql_effsat_no_columns_valid():
    """EffSat with empty columns still produces valid MERGE SQL (no trailing comma)."""
    model = DataVaultModel(
        effsats={
            "s.EmptyEffSat": EffSat(
                name="EmptyEffSat", namespace="s", parent_ref="SomeLink", columns=[]
            )
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    assert "satellites/effsat_EmptyEffSat.sql" in result.files
    sql = result.files["satellites/effsat_EmptyEffSat.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql


# --- SQL Jinja SamLink tests ---


def test_sql_samlink_output_valid():
    """SamLink SQL uses MERGE INTO, samlink_name_hk as key, master/duplicate refs, columns rendered."""
    gen = registry.get("sql-jinja")
    result = gen.generate(_sample_model_with_effsat_samlink())
    assert "links/samlink_CustomerMatch.sql" in result.files
    sql = result.files["links/samlink_CustomerMatch.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql
    assert "CustomerMatch_hk" in sql
    assert "Customer_hk" in sql
    assert "confidence" in sql


def test_sql_samlink_no_columns_valid():
    """SamLink with empty columns still produces valid MERGE SQL."""
    model = DataVaultModel(
        samlinks={
            "s.EmptySam": SamLink(
                name="EmptySam", namespace="s", master_ref="HubA", duplicate_ref="HubA", columns=[]
            )
        },
    )
    gen = registry.get("sql-jinja")
    result = gen.generate(model)
    assert "links/samlink_EmptySam.sql" in result.files
    sql = result.files["links/samlink_EmptySam.sql"]
    _assert_valid_sql(sql)
    assert "MERGE INTO" in sql


# --- Spark DLT EffSat / SamLink tests ---


def test_spark_effsat_output_functional():
    """EffSat Spark code uses dlt.apply_changes with stored_as_scd_type=1, parent_ref_hk key."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_effsat_samlink())
    assert "satellites/effsat_CustProdValidity.py" in result.files
    code = result.files["satellites/effsat_CustProdValidity.py"]
    assert "import dlt" in code
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code
    assert "CustomerProduct_hk" in code
    assert "effsat_CustProdValidity" in code
    # apply_changes infers schema at runtime — column names must NOT appear
    assert "valid_from" not in code
    assert "valid_to" not in code


def test_spark_samlink_output_functional():
    """SamLink Spark code uses dlt.apply_changes with stored_as_scd_type=1, samlink_name_hk key."""
    gen = registry.get("spark-declarative")
    result = gen.generate(_sample_model_with_effsat_samlink())
    assert "links/samlink_CustomerMatch.py" in result.files
    code = result.files["links/samlink_CustomerMatch.py"]
    assert "import dlt" in code
    assert "apply_changes" in code
    assert "stored_as_scd_type=1" in code
    assert "CustomerMatch_hk" in code
    assert "samlink_CustomerMatch" in code
    # apply_changes infers schema at runtime — column names must NOT appear
    assert "confidence" not in code
