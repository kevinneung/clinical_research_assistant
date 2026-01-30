"""Tests for the export service."""

import pytest
from pathlib import Path
import tempfile
import shutil
import csv

from src.services.export_service import ExportService


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def export_service(temp_workspace):
    """Create an export service with temporary workspace."""
    return ExportService(temp_workspace)


class TestExportService:
    """Tests for ExportService."""

    def test_export_to_csv(self, export_service):
        """Test basic CSV export."""
        data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
        ]

        filepath = export_service.export_to_csv(data, "test_export")

        assert filepath.exists()
        assert filepath.suffix == ".csv"

        # Verify content
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["name"] == "Item 1"
        assert rows[1]["value"] == "200"

    def test_export_to_csv_with_fieldnames(self, export_service):
        """Test CSV export with specified field order."""
        data = [
            {"c": 3, "b": 2, "a": 1},
        ]

        filepath = export_service.export_to_csv(
            data,
            "ordered",
            fieldnames=["a", "b", "c"],
        )

        with open(filepath, "r", encoding="utf-8") as f:
            header = f.readline().strip()

        assert header == "a,b,c"

    def test_export_empty_csv(self, export_service):
        """Test exporting empty data."""
        filepath = export_service.export_to_csv([], "empty")

        assert filepath.exists()

    def test_export_cost_estimate(self, export_service):
        """Test exporting a cost estimate."""
        estimate = {
            "material_costs": [
                {
                    "category": "Supplies",
                    "description": "Lab supplies",
                    "estimated_cost": 1000,
                    "currency": "USD",
                    "source": "Estimate",
                    "confidence": "medium",
                }
            ],
            "labor_costs": [
                {
                    "category": "Personnel",
                    "description": "Research assistant",
                    "estimated_cost": 5000,
                    "currency": "USD",
                    "source": "Market rate",
                    "confidence": "high",
                }
            ],
            "regulatory_costs": [],
            "other_costs": [],
            "total_estimated_cost": 6000,
        }

        filepath = export_service.export_cost_estimate(estimate)

        assert filepath.exists()
        assert "cost_estimate" in filepath.name

        # Verify content includes total
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "TOTAL" in content
        assert "6000" in content

    def test_export_to_markdown(self, export_service):
        """Test Markdown export."""
        content = "# Test Document\n\nSome content here."
        metadata = {"title": "Test", "author": "Tester"}

        filepath = export_service.export_to_markdown(
            content,
            "test_doc",
            metadata=metadata,
        )

        assert filepath.exists()
        assert filepath.suffix == ".md"

        with open(filepath, "r", encoding="utf-8") as f:
            file_content = f.read()

        assert "---" in file_content  # YAML frontmatter
        assert "title: Test" in file_content
        assert "# Test Document" in file_content

    def test_list_exports(self, export_service):
        """Test listing export files."""
        # Create some exports
        export_service.export_to_csv([{"a": 1}], "export1")
        export_service.export_to_csv([{"b": 2}], "export2")

        exports = export_service.list_exports()

        assert len(exports) == 2
        names = [e["name"] for e in exports]
        assert "export1.csv" in names
        assert "export2.csv" in names
