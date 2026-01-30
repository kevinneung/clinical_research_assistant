"""Filesystem MCP server setup utilities."""

from pathlib import Path
from pydantic_ai.mcp import MCPServerStdio


def create_filesystem_server(workspace_path: str | Path) -> MCPServerStdio:
    """Create a filesystem MCP server for the given workspace.

    Args:
        workspace_path: Path to the workspace directory.

    Returns:
        Configured MCPServerStdio instance for filesystem operations.
    """
    workspace_path = str(Path(workspace_path).resolve())

    return MCPServerStdio(
        "npx",
        args=["-y", "@anthropic/mcp-server-filesystem", workspace_path],
    )
