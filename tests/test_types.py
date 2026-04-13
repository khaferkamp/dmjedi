"""Tests for the shared DVML type mapping module (model/types.py)."""

from dmjedi.model.types import SUPPORTED_DIALECTS, map_pyspark_type, map_type


def test_map_type_bigint_all_dialects():
    assert map_type("bigint", "default") == "BIGINT"
    assert map_type("bigint", "postgres") == "BIGINT"
    assert map_type("bigint", "spark") == "BIGINT"


def test_map_type_float_all_dialects():
    assert map_type("float", "default") == "FLOAT"
    assert map_type("float", "postgres") == "DOUBLE PRECISION"
    assert map_type("float", "spark") == "FLOAT"


def test_map_type_varchar_default_bare():
    """D-16: bare varchar defaults to VARCHAR(255) (or dialect-specific)."""
    assert map_type("varchar", "default") == "VARCHAR(255)"
    assert map_type("varchar", "postgres") == "VARCHAR(255)"
    assert map_type("varchar", "spark") == "STRING"


def test_map_type_varchar_parameterized():
    """D-13: parameter-aware mapping for varchar(100)."""
    assert map_type("varchar(100)", "default") == "VARCHAR(100)"
    assert map_type("varchar(100)", "postgres") == "VARCHAR(100)"
    assert map_type("varchar(100)", "spark") == "STRING(100)"


def test_map_type_decimal_parameterized():
    """D-13: parameter-aware mapping for decimal(10,4)."""
    assert map_type("decimal(10,4)", "default") == "DECIMAL(10,4)"


def test_map_type_binary_all_dialects():
    assert map_type("binary", "default") == "BINARY"
    assert map_type("binary", "postgres") == "BYTEA"
    assert map_type("binary", "spark") == "BINARY"


def test_map_pyspark_type_new_types():
    assert map_pyspark_type("bigint") == "LongType()"
    assert map_pyspark_type("float") == "FloatType()"
    assert map_pyspark_type("varchar") == "StringType()"
    assert map_pyspark_type("binary") == "BinaryType()"


def test_map_pyspark_type_parameterized_ignores_params():
    """PySpark types ignore varchar parameters."""
    assert map_pyspark_type("varchar(100)") == "StringType()"


def test_map_pyspark_type_decimal_preserves_params():
    """PySpark decimal preserves precision/scale."""
    assert map_pyspark_type("decimal(10,4)") == "DecimalType(10,4)"


def test_existing_types_unchanged():
    """Regression: all 7 original types still map correctly."""
    assert map_type("int") == "INT"
    assert map_type("string") == "VARCHAR(255)"
    assert map_type("decimal") == "DECIMAL(18,2)"
    assert map_type("date") == "DATE"
    assert map_type("timestamp") == "TIMESTAMP"
    assert map_type("boolean") == "BOOLEAN"
    assert map_type("json") == "JSON"
    # Postgres
    assert map_type("string", "postgres") == "TEXT"
    assert map_type("json", "postgres") == "JSONB"
    # Spark
    assert map_type("string", "spark") == "STRING"


def test_supported_dialects():
    assert {"default", "postgres", "spark"}.issubset(set(SUPPORTED_DIALECTS))
    assert "duckdb" in SUPPORTED_DIALECTS
    assert "databricks" in SUPPORTED_DIALECTS


# --- System type entries (D-03, D-04, D-05) ---


class TestSystemTypeEntries:
    """Tests for system column type mapping via map_type() (GEN-02, D-03)."""

    def test_system_type_hashkey_default(self):
        """hashkey maps to BINARY for default dialect (matches current hardcoded value)."""
        assert map_type("hashkey", "default") == "BINARY"

    def test_system_type_hashkey_postgres(self):
        assert map_type("hashkey", "postgres") == "BYTEA"

    def test_system_type_hashkey_duckdb(self):
        assert map_type("hashkey", "duckdb") == "BLOB"

    def test_system_type_hashkey_databricks(self):
        assert map_type("hashkey", "databricks") == "BINARY"

    def test_system_type_load_ts_default(self):
        """load_ts maps to TIMESTAMP for default dialect (matches current hardcoded value)."""
        assert map_type("load_ts", "default") == "TIMESTAMP"

    def test_system_type_load_ts_postgres(self):
        assert map_type("load_ts", "postgres") == "TIMESTAMP"

    def test_system_type_load_ts_duckdb(self):
        assert map_type("load_ts", "duckdb") == "TIMESTAMP"

    def test_system_type_record_source_default(self):
        """record_source maps to VARCHAR(255) for default dialect."""
        assert map_type("record_source", "default") == "VARCHAR(255)"

    def test_system_type_record_source_postgres(self):
        assert map_type("record_source", "postgres") == "TEXT"

    def test_system_type_record_source_duckdb(self):
        assert map_type("record_source", "duckdb") == "VARCHAR"

    def test_system_type_record_source_databricks(self):
        assert map_type("record_source", "databricks") == "STRING"

    def test_system_type_hash_diff_default(self):
        """hash_diff maps to BINARY for default dialect (matches current hardcoded value)."""
        assert map_type("hash_diff", "default") == "BINARY"

    def test_system_type_hash_diff_postgres(self):
        assert map_type("hash_diff", "postgres") == "BYTEA"

    def test_system_type_hash_diff_duckdb(self):
        assert map_type("hash_diff", "duckdb") == "BLOB"

    def test_system_type_hash_diff_databricks(self):
        assert map_type("hash_diff", "databricks") == "BINARY"


class TestSupportedDialectsExtended:
    """Tests for D-08: SUPPORTED_DIALECTS derived dynamically from _TYPE_MAP."""

    def test_supported_dialects_includes_duckdb(self):
        assert "duckdb" in SUPPORTED_DIALECTS

    def test_supported_dialects_includes_databricks(self):
        assert "databricks" in SUPPORTED_DIALECTS

    def test_supported_dialects_includes_original(self):
        """Original dialects still present after extension."""
        for d in ["default", "postgres", "spark"]:
            assert d in SUPPORTED_DIALECTS

    def test_existing_types_unchanged_after_system_types(self):
        """Regression: adding system types does not change existing user type mappings."""
        assert map_type("int") == "INT"
        assert map_type("string") == "VARCHAR(255)"
        assert map_type("decimal") == "DECIMAL(18,2)"
        assert map_type("binary") == "BINARY"
        assert map_type("string", "postgres") == "TEXT"
        assert map_type("json", "postgres") == "JSONB"
        assert map_type("string", "spark") == "STRING"
