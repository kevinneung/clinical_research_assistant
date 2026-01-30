"""Email MCP server setup utilities."""

from typing import Any


def create_email_server(server_url: str = "http://localhost:3001/mcp") -> Any | None:
    """Create an email MCP server connection.

    Note: Email MCP server requires a separate server process running.
    This is optional functionality.

    Args:
        server_url: URL of the email MCP server.

    Returns:
        Configured MCP server instance, or None if not available.
    """
    # Email MCP integration would use MCPServerHTTP when available
    # For now, return None as this is optional functionality
    return None
