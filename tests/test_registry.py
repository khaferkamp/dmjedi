"""Tests for the generator registry factory pattern (GEN-01)."""

import re
from pathlib import Path
from typing import ClassVar

import pytest

from dmjedi.generators import registry
from dmjedi.generators.base import BaseGenerator
from dmjedi.generators.spark_declarative.generator import SparkDeclarativeGenerator
from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator


class TestRegistryFactoryPattern:
    """Tests for D-01: registry stores classes, get() instantiates with params."""

    def test_registry_stores_classes(self):
        """Registry values must be classes (type), not instances."""
        for name, entry in registry._REGISTRY.items():
            assert isinstance(entry, type), (
                f"Registry entry '{name}' is {type(entry).__name__}, expected a class (type). "
                "Per D-01, registry must store generator classes, not instances."
            )

    def test_registry_get_returns_instance(self):
        """get() must return a new instance, not a stored singleton."""
        gen = registry.get("sql-jinja")
        assert isinstance(gen, BaseGenerator)
        assert isinstance(gen, SqlJinjaGenerator)

    def test_registry_get_with_dialect_param(self):
        """get() must pass dialect param to constructor (D-01, D-07)."""
        gen = registry.get("sql-jinja", dialect="postgres")
        assert isinstance(gen, SqlJinjaGenerator)
        assert gen._dialect == "postgres"

    def test_registry_get_spark_with_kwargs(self):
        """SparkDeclarative must accept kwargs without TypeError (D-02)."""
        gen = registry.get("spark-declarative", dialect="default")
        assert isinstance(gen, SparkDeclarativeGenerator)

    def test_registry_get_unknown_raises(self):
        """Unknown generator name raises KeyError with helpful message."""
        with pytest.raises(KeyError, match="Unknown generator"):
            registry.get("nonexistent")

    def test_registry_available_lists_builtins(self):
        """available() returns registered generator names."""
        names = registry.available()
        assert "spark-declarative" in names
        assert "sql-jinja" in names


class TestTemplateNoHardcodedTypes:
    """Tests for GEN-02: no hardcoded system column types in templates."""

    TEMPLATES_DIR = Path("src/dmjedi/generators/sql_jinja/templates")
    # Templates that declare DDL columns (CREATE TABLE with type declarations)
    DDL_TEMPLATES: ClassVar[list[str]] = ["hub.sql.j2", "satellite.sql.j2", "link.sql.j2"]

    def test_no_hardcoded_binary_in_ddl_templates(self):
        """DDL templates must not contain bare ' BINARY' type declarations."""
        for tpl_name in self.DDL_TEMPLATES:
            content = (self.TEMPLATES_DIR / tpl_name).read_text()
            # Match BINARY that is NOT inside a map_type() call
            # Remove all map_type(...) calls first, then check for BINARY
            stripped = re.sub(r'\{\{.*?map_type\(.*?\).*?\}\}', '', content)
            assert " BINARY" not in stripped, (
                f"{tpl_name} contains hardcoded ' BINARY' outside map_type(). "
                "Per D-03, all system column types must use map_type()."
            )

    def test_no_hardcoded_timestamp_in_ddl_templates(self):
        """DDL templates must not contain bare ' TIMESTAMP' type declarations."""
        for tpl_name in self.DDL_TEMPLATES:
            content = (self.TEMPLATES_DIR / tpl_name).read_text()
            stripped = re.sub(r'\{\{.*?map_type\(.*?\).*?\}\}', '', content)
            assert " TIMESTAMP" not in stripped, (
                f"{tpl_name} contains hardcoded ' TIMESTAMP' outside map_type(). "
                "Per D-03, all system column types must use map_type()."
            )
