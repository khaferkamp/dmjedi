"""Generator registry — discovers and manages available generators."""

from dmjedi.generators.base import BaseGenerator

_REGISTRY: dict[str, BaseGenerator] = {}


def register(generator: BaseGenerator) -> None:
    """Register a generator instance."""
    _REGISTRY[generator.name] = generator


def get(name: str) -> BaseGenerator:
    """Get a generator by name. Raises KeyError if not found."""
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        msg = f"Unknown generator '{name}'. Available: {available}"
        raise KeyError(msg)
    return _REGISTRY[name]


def available() -> list[str]:
    """List registered generator names."""
    return sorted(_REGISTRY.keys())


def _auto_register() -> None:
    """Register built-in generators."""
    from dmjedi.generators.spark_declarative.generator import SparkDeclarativeGenerator
    from dmjedi.generators.sql_jinja.generator import SqlJinjaGenerator

    register(SparkDeclarativeGenerator())
    register(SqlJinjaGenerator())


_auto_register()
