"""Thin MCP tool adapters over the shared application services."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from dmjedi.application.requests import CompileRequest
from dmjedi.application.services import explain_request, generate_request, validate_request


def validate(
    source: str | None = None,
    path: str | None = None,
    source_name: str = "<string>",
) -> dict[str, object]:
    """Validate DVML from inline source or a filesystem path."""
    request = _build_request(source=source, path=path, source_name=source_name)
    result = validate_request(request)
    return result.model_dump(mode="json")


def generate(
    source: str | None = None,
    path: str | None = None,
    source_name: str = "<string>",
    target: str = "spark-declarative",
    dialect: str = "default",
) -> dict[str, object]:
    """Generate in-memory artifacts from inline source or a filesystem path."""
    request = _build_request(source=source, path=path, source_name=source_name)
    result = generate_request(request, target=target, dialect=dialect)
    return result.model_dump(mode="json")


def explain(
    source: str | None = None,
    path: str | None = None,
    source_name: str = "<string>",
) -> dict[str, object]:
    """Explain the resolved model from inline source or a filesystem path."""
    request = _build_request(source=source, path=path, source_name=source_name)
    result = explain_request(request)
    return result.model_dump(mode="json")


def register_tools(server: FastMCP) -> None:
    """Register the locked DMJedi MCP tool surface."""
    for tool in (validate, generate, explain):
        server.add_tool(tool, structured_output=True)


def _build_request(
    *,
    source: str | None,
    path: str | None,
    source_name: str,
) -> CompileRequest:
    if source is None and path is None:
        msg = "either source or path must be provided"
        raise ValueError(msg)

    if source is not None and path is not None:
        msg = "source and path are mutually exclusive"
        raise ValueError(msg)

    if path is not None:
        return CompileRequest(paths=[Path(path)])

    return CompileRequest(source=source, source_name=source_name)
