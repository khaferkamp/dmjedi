"""Generator registry — discovers and manages available generators."""

from __future__ import annotations

from typing import Any

from dmjedi.generators.base import BaseGenerator

_REGISTRY: dict[str, type[BaseGenerator]] = {}


def register(generator_cls: type[BaseGenerator]) -> None:
    """Register a generator class."""
    instance = generator_cls()
    _REGISTRY[instance.name] = generator_cls


def get(name: str, **kwargs: Any) -> BaseGenerator:
    """Get a generator by name, instantiated with the given kwargs.

    Raises KeyError if not found.

    Examples:
        registry.get("sql-jinja")
        registry.get("sql-jinja", dialect="duckdb")
        registry.get("sql-jinja", dialect="duckdb", hash_algo="sha256")
    """
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        msg = f"Unknown generator '{name}'. Available: {available}"
        raise KeyError(msg)
    return _REGISTRY[name](**kwargs)


def available() -> list[str]:
    """List registered generator names."""
    return sorted(_REGISTRY.keys())


def _auto_register() -> None:
    """Register built-in generators."""
    from dmjedi.generators.spark_declarative.generator import SparkDeclarativeGenerator
    from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator

    register(SparkDeclarativeGenerator)
    register(SqlJinjaGenerator)


_auto_register()
