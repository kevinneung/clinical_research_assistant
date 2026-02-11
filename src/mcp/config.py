"""MCP server configuration and loader."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_ai.mcp import MCPServerStdio


@dataclass
class MCPToolsets:
    """Container for MCP server connections."""

    filesystem: MCPServerStdio | None = None
    web_search: MCPServerStdio | None = None
    email: Any | None = None  # MCPServerHTTP when available


def create_mcp_toolsets(
    workspace_path: str | Path,
    npx_available: bool = True,
) -> MCPToolsets:
    """Create MCP server connections for agent use.

    Args:
        workspace_path: Path to the workspace directory for filesystem access.
        npx_available: Whether npx is available on the system.

    Returns:
        MCPToolsets containing configured MCP servers.
    """
    if not npx_available:
        return MCPToolsets()

    workspace_path = str(Path(workspace_path).resolve())

    # Filesystem MCP server - always available
    # timeout=30 because npx may need to download the package on first run
    filesystem = MCPServerStdio(
        "npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", workspace_path],
        timeout=30,
    )

    # Web search MCP server - requires BRAVE_API_KEY
    web_search = None
    brave_api_key = os.environ.get("BRAVE_API_KEY")
    if brave_api_key:
        web_search = MCPServerStdio(
            "npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": brave_api_key},
            timeout=30,
        )

    return MCPToolsets(
        filesystem=filesystem,
        web_search=web_search,
        email=None,  # Email MCP setup would go here
    )


def get_mcp_servers_for_agent(toolsets: MCPToolsets) -> list:
    """Get list of active MCP servers for agent configuration.

    Args:
        toolsets: MCPToolsets instance with configured servers.

    Returns:
        List of active MCP server instances.
    """
    servers = []

    if toolsets.filesystem is not None:
        servers.append(toolsets.filesystem)

    if toolsets.web_search is not None:
        servers.append(toolsets.web_search)

    if toolsets.email is not None:
        servers.append(toolsets.email)

    return servers
