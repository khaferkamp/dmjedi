"""DMJedi MCP server bootstrap."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from dmjedi.mcp.tools import register_tools

SERVER = FastMCP("dmjedi")
register_tools(SERVER)


def start_server() -> None:
    """Start the DMJedi MCP server over stdio."""
    SERVER.run(transport="stdio")
