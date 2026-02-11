"""Web search MCP server setup utilities."""

import os
from pydantic_ai.mcp import MCPServerStdio


def create_web_search_server(api_key: str | None = None) -> MCPServerStdio | None:
    """Create a web search MCP server using Brave Search.

    Args:
        api_key: Brave Search API key. If not provided, uses BRAVE_API_KEY env var.

    Returns:
        Configured MCPServerStdio instance, or None if no API key available.
    """
    api_key = api_key or os.environ.get("BRAVE_API_KEY")

    if not api_key:
        return None

    return MCPServerStdio(
        "npx",
        args=["-y", "@anthropic/mcp-server-brave-search"],
        env={"BRAVE_API_KEY": api_key},
        timeout=30,
    )
