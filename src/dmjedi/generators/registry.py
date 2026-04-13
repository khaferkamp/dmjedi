"""Generator registry -- discovers and manages available generators."""

from __future__ import annotations

from typing import Any

from dmjedi.generators.base import BaseGenerator

_REGISTRY: dict[str, type[BaseGenerator]] = {}


def register(cls: type[BaseGenerator], name: str) -> None:
    """Register a generator class by name."""
    _REGISTRY[name] = cls


def get(name: str, **params: Any) -> BaseGenerator:
    """Instantiate a generator by name with parameters.

    Raises KeyError if the generator name is not registered.
    """
    if name not in _REGISTRY:
        available_names = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        msg = f"Unknown generator '{name}'. Available: {available_names}"
        raise KeyError(msg)
    return _REGISTRY[name](**params)


def available() -> list[str]:
    """List registered generator names."""
    return sorted(_REGISTRY.keys())


def _auto_register() -> None:
    """Register built-in generators."""
    from dmjedi.generators.spark_declarative.generator import SparkDeclarativeGenerator
    from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator

    register(SparkDeclarativeGenerator, "spark-declarative")
    register(SqlJinjaGenerator, "sql-jinja")


_auto_register()
