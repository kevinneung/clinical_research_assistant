"""Tests for the workspace manager service."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.services.workspace_manager import WorkspaceManager


@pytest.fixture
def temp_base_path():
    """Create a temporary base path for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def workspace_manager(temp_base_path):
    """Create a workspace manager with temporary base path."""
    return WorkspaceManager(temp_base_path)


class TestWorkspaceManager:
    """Tests for WorkspaceManager."""

    def test_create_workspace(self, workspace_manager, temp_base_path):
        """Test creating a new workspace."""
        workspace_path = workspace_manager.create_workspace("Test Project")

        assert workspace_path.exists()
        assert workspace_path.is_dir()
        assert (workspace_path / "documents").exists()
        assert (workspace_path / "drafts").exists()
        assert (workspace_path / "exports").exists()

    def test_create_workspace_sanitizes_name(self, workspace_manager):
        """Test that workspace creation sanitizes project names."""
        workspace_path = workspace_manager.create_workspace("Test/Project:With*Special")

        assert workspace_path.exists()
        # Name should not contain special characters
        assert "/" not in workspace_path.name
        assert ":" not in workspace_path.name
        assert "*" not in workspace_path.name

    def test_list_workspaces(self, workspace_manager):
        """Test listing workspaces."""
        # Create some workspaces
        workspace_manager.create_workspace("Project 1")
        workspace_manager.create_workspace("Project 2")

        workspaces = workspace_manager.list_workspaces()

        assert len(workspaces) == 2

    def test_delete_workspace(self, workspace_manager):
        """Test deleting a workspace."""
        workspace_path = workspace_manager.create_workspace("To Delete")

        assert workspace_path.exists()

        result = workspace_manager.delete_workspace(workspace_path)

        assert result is True
        assert not workspace_path.exists()

    def test_delete_nonexistent_workspace(self, workspace_manager):
        """Test deleting a workspace that doesn't exist."""
        result = workspace_manager.delete_workspace("/nonexistent/path")

        assert result is False

    def test_write_and_read_document(self, workspace_manager):
        """Test writing and reading a document."""
        workspace_path = workspace_manager.create_workspace("Doc Test")

        # Write a document
        file_path = workspace_manager.write_document(
            workspace_path,
            "test.txt",
            "Hello, World!",
        )

        assert file_path.exists()

        # Read it back
        content = workspace_manager.read_document(file_path)

        assert content == "Hello, World!"

    def test_write_document_to_subdirectory(self, workspace_manager):
        """Test writing a document to a subdirectory."""
        workspace_path = workspace_manager.create_workspace("Subdir Test")

        file_path = workspace_manager.write_document(
            workspace_path,
            "nested.txt",
            "Nested content",
            subdirectory="deep/nested",
        )

        assert file_path.exists()
        assert "deep" in str(file_path)
        assert "nested" in str(file_path)

    def test_list_documents(self, workspace_manager):
        """Test listing documents in a workspace."""
        workspace_path = workspace_manager.create_workspace("List Test")

        # Create some documents
        workspace_manager.write_document(workspace_path, "doc1.txt", "Content 1")
        workspace_manager.write_document(workspace_path, "doc2.md", "Content 2")

        documents = workspace_manager.list_documents(workspace_path)

        # Should include our documents (plus any default files)
        doc_names = [d["name"] for d in documents]
        assert "doc1.txt" in doc_names
        assert "doc2.md" in doc_names

    def test_get_workspace_stats(self, workspace_manager):
        """Test getting workspace statistics."""
        workspace_path = workspace_manager.create_workspace("Stats Test")

        # Add some content
        workspace_manager.write_document(workspace_path, "file1.txt", "A" * 100)
        workspace_manager.write_document(workspace_path, "file2.txt", "B" * 200)

        stats = workspace_manager.get_workspace_stats(workspace_path)

        assert stats["file_count"] >= 2
        assert stats["total_size_bytes"] >= 300
