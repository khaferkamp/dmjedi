"""DVML to SQL type mapping per dialect.

Delegates to the shared type module. Kept for backward compatibility.
"""
from dmjedi.model.types import SUPPORTED_DIALECTS, map_type

__all__ = ["SUPPORTED_DIALECTS", "map_type"]
