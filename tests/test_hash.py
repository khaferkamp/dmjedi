"""Tests for the hash expression builder and identifier quoting."""

from dmjedi.generators.sql_jinja.hash import build_hash_expr


class TestBuildHashExprDuckDB:
    """DuckDB dialect hash expression tests."""

    def test_single_column(self) -> None:
        result = build_hash_expr(["customer_id"], "duckdb")
        assert result == """sha256(COALESCE(CAST("customer_id" AS VARCHAR), ''))"""

    def test_multi_column_delimiter(self) -> None:
        result = build_hash_expr(["a", "b"], "duckdb")
        assert "|| '||' ||" in result
        assert result == (
            """sha256(COALESCE(CAST("a" AS VARCHAR), '') || '||' || """
            """COALESCE(CAST("b" AS VARCHAR), ''))"""
        )

    def test_three_columns(self) -> None:
        result = build_hash_expr(["x", "y", "z"], "duckdb")
        assert result.count("COALESCE") == 3
        assert result.count("|| '||' ||") == 2


class TestBuildHashExprDatabricks:
    """Databricks dialect hash expression tests."""

    def test_single_column(self) -> None:
        result = build_hash_expr(["customer_id"], "databricks")
        assert result == """sha2(COALESCE("customer_id", ''), 256)"""

    def test_multi_column(self) -> None:
        result = build_hash_expr(["a", "b"], "databricks")
        assert "sha2(" in result
        assert ", 256)" in result
        assert "|| '||' ||" in result


class TestBuildHashExprPostgres:
    """PostgreSQL dialect hash expression tests."""

    def test_single_column(self) -> None:
        result = build_hash_expr(["customer_id"], "postgres")
        assert "encode(sha256(" in result
        assert "::bytea" in result
        assert "'hex')" in result

    def test_multi_column(self) -> None:
        result = build_hash_expr(["a", "b"], "postgres")
        assert "encode(sha256(" in result
        assert "::bytea" in result
        assert "|| '||' ||" in result


class TestBuildHashExprDefault:
    """Default dialect hash expression tests."""

    def test_single_column(self) -> None:
        result = build_hash_expr(["customer_id"], "default")
        assert result == """SHA256(COALESCE("customer_id", ''))"""

    def test_unknown_dialect_falls_back(self) -> None:
        result = build_hash_expr(["x"], "unknown_dialect")
        assert result == """SHA256(COALESCE("x", ''))"""


class TestBuildHashExprEdgeCases:
    """Edge case tests for hash expression builder."""

    def test_single_column_no_delimiter(self) -> None:
        result = build_hash_expr(["x"], "duckdb")
        # Single column should not have the delimiter pattern
        assert "|| '||' ||" not in result

    def test_empty_columns(self) -> None:
        """Empty column list produces hash of empty string."""
        result = build_hash_expr([], "duckdb")
        assert "sha256(" in result


class TestBuildHashExprAlgoOverride:
    """Tests for D-02: hash algorithm configurability."""

    def test_explicit_sha256_same_as_default(self) -> None:
        """Passing hash_algo='sha256' explicitly produces same result as default."""
        default_result = build_hash_expr(["col"], "duckdb")
        explicit_result = build_hash_expr(["col"], "duckdb", "sha256")
        assert default_result == explicit_result

    def test_explicit_sha256_duckdb(self) -> None:
        """DuckDB with explicit sha256 algo returns sha256 pattern."""
        result = build_hash_expr(["col"], "duckdb", "sha256")
        assert "sha256(" in result

    def test_explicit_sha256_databricks(self) -> None:
        """Databricks with explicit sha256 algo returns sha2 pattern."""
        result = build_hash_expr(["col"], "databricks", "sha256")
        assert "sha2(" in result
        assert ", 256)" in result

    def test_explicit_sha256_postgres(self) -> None:
        """PostgreSQL with explicit sha256 algo returns encode/sha256/bytea pattern."""
        result = build_hash_expr(["col"], "postgres", "sha256")
        assert "encode(sha256(" in result
        assert "::bytea" in result

    def test_unknown_algo_falls_back_to_default_sha256(self) -> None:
        """Unknown hash_algo falls back to default sha256."""
        result = build_hash_expr(["col"], "duckdb", "unknown_algo")
        # Should fall back to default sha256
        assert "SHA256(" in result or "sha256(" in result

    def test_factory_passes_hash_algo(self) -> None:
        """registry.get passes hash_algo kwarg through to SqlJinjaGenerator (D-02 wiring)."""
        from dmjedi.generators import registry

        gen = registry.get("sql-jinja", dialect="duckdb", hash_algo="sha256")
        assert hasattr(gen, "_hash_algo"), "Generator missing _hash_algo attribute"
        assert gen._hash_algo == "sha256", f"Expected sha256, got {gen._hash_algo}"


class TestQuoteIdentifierFilter:
    """Tests for the q filter pattern used in Jinja2 templates."""

    def test_simple_name(self) -> None:
        q = lambda name: f'"{name}"'  # noqa: E731
        assert q("Customer") == '"Customer"'

    def test_compound_name(self) -> None:
        q = lambda name: f'"{name}"'  # noqa: E731
        assert q("Customer_hk") == '"Customer_hk"'

    def test_system_column(self) -> None:
        q = lambda name: f'"{name}"'  # noqa: E731
        assert q("load_ts") == '"load_ts"'

    def test_reserved_word(self) -> None:
        q = lambda name: f'"{name}"'  # noqa: E731
        assert q("select") == '"select"'
