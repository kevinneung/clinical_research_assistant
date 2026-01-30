"""Workspace manager for file and directory operations."""

import shutil
from pathlib import Path
from datetime import datetime


class WorkspaceManager:
    """Manages project workspace directories and files."""

    def __init__(self, base_path: str | Path | None = None):
        """Initialize the workspace manager.

        Args:
            base_path: Base directory for all workspaces. Defaults to user's home.
        """
        if base_path is None:
            base_path = Path.home() / ".clinical_research_assistant" / "workspaces"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, project_name: str) -> Path:
        """Create a new workspace directory for a project.

        Args:
            project_name: Name of the project.

        Returns:
            Path to the created workspace.
        """
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in project_name)
        safe_name = safe_name.strip().replace(" ", "_")

        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace_name = f"{safe_name}_{timestamp}"

        workspace_path = self.base_path / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        (workspace_path / "documents").mkdir(exist_ok=True)
        (workspace_path / "drafts").mkdir(exist_ok=True)
        (workspace_path / "exports").mkdir(exist_ok=True)

        return workspace_path

    def get_workspace(self, workspace_path: str | Path) -> Path | None:
        """Get a workspace path if it exists.

        Args:
            workspace_path: Path to the workspace.

        Returns:
            Path if exists, None otherwise.
        """
        path = Path(workspace_path)
        if path.exists() and path.is_dir():
            return path
        return None

    def list_workspaces(self) -> list[Path]:
        """List all existing workspaces.

        Returns:
            List of workspace paths.
        """
        if not self.base_path.exists():
            return []

        return [p for p in self.base_path.iterdir() if p.is_dir()]

    def delete_workspace(self, workspace_path: str | Path) -> bool:
        """Delete a workspace and all its contents.

        Args:
            workspace_path: Path to the workspace.

        Returns:
            True if deleted, False if not found.
        """
        path = Path(workspace_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            return True
        return False

    def list_documents(self, workspace_path: str | Path) -> list[dict]:
        """List all documents in a workspace.

        Args:
            workspace_path: Path to the workspace.

        Returns:
            List of document info dictionaries.
        """
        path = Path(workspace_path)
        documents = []

        for doc_path in path.rglob("*"):
            if doc_path.is_file():
                rel_path = doc_path.relative_to(path)
                documents.append({
                    "name": doc_path.name,
                    "path": str(doc_path),
                    "relative_path": str(rel_path),
                    "size": doc_path.stat().st_size,
                    "modified": datetime.fromtimestamp(doc_path.stat().st_mtime),
                    "type": doc_path.suffix.lower(),
                })

        return documents

    def read_document(self, file_path: str | Path) -> str | None:
        """Read a document's contents.

        Args:
            file_path: Path to the document.

        Returns:
            Document contents as string, or None if not readable.
        """
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                return path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return None
        return None

    def write_document(
        self,
        workspace_path: str | Path,
        filename: str,
        content: str,
        subdirectory: str = "",
    ) -> Path:
        """Write content to a document in the workspace.

        Args:
            workspace_path: Path to the workspace.
            filename: Name of the file.
            content: Content to write.
            subdirectory: Optional subdirectory within workspace.

        Returns:
            Path to the written file.
        """
        path = Path(workspace_path)
        if subdirectory:
            path = path / subdirectory
            path.mkdir(parents=True, exist_ok=True)

        file_path = path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def copy_file(
        self,
        source: str | Path,
        workspace_path: str | Path,
        subdirectory: str = "",
    ) -> Path:
        """Copy a file into the workspace.

        Args:
            source: Source file path.
            workspace_path: Target workspace path.
            subdirectory: Optional subdirectory within workspace.

        Returns:
            Path to the copied file.
        """
        source_path = Path(source)
        dest_dir = Path(workspace_path)

        if subdirectory:
            dest_dir = dest_dir / subdirectory
            dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        return dest_path

    def get_workspace_stats(self, workspace_path: str | Path) -> dict:
        """Get statistics about a workspace.

        Args:
            workspace_path: Path to the workspace.

        Returns:
            Dictionary with workspace statistics.
        """
        path = Path(workspace_path)

        if not path.exists():
            return {"error": "Workspace not found"}

        files = list(path.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        dir_count = sum(1 for f in files if f.is_dir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        return {
            "path": str(path),
            "file_count": file_count,
            "directory_count": dir_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
