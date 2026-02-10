"""Shared agent dependencies and types."""

from dataclasses import dataclass
from typing import Awaitable, Callable, Any

from sqlalchemy.orm import Session


@dataclass
class AgentDeps:
    """Shared dependencies injected into all agents.

    Attributes:
        db_session: SQLAlchemy database session for persistence.
        workspace_path: Path to the project workspace directory.
        project_id: ID of the current project.
        mcp_filesystem: MCP server for filesystem operations.
        mcp_web_search: MCP server for web search (optional).
        mcp_email: MCP server for email operations (optional).
        approval_callback: Async function to request human approval.
        progress_callback: Function to send progress updates to UI.
    """

    db_session: Session
    workspace_path: str
    project_id: int
    mcp_filesystem: Any  # MCPServerStdio
    mcp_web_search: Any | None  # MCPServerStdio | None
    mcp_email: Any | None  # MCPServerHTTP | None
    approval_callback: Callable[[str, dict], Awaitable[bool]]
    progress_callback: Callable[[str, str], None]
    question_callback: Callable[[str, list[str]], Awaitable[str]]

    def get_active_mcp_servers(self) -> list:
        """Get list of active MCP servers."""
        servers = [self.mcp_filesystem]
        if self.mcp_web_search is not None:
            servers.append(self.mcp_web_search)
        if self.mcp_email is not None:
            servers.append(self.mcp_email)
        return servers
