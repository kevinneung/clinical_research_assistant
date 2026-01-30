"""Export service for generating CSV and document exports."""

import csv
from pathlib import Path
from datetime import datetime
from typing import Any


class ExportService:
    """Service for exporting data to various formats."""

    def __init__(self, workspace_path: str | Path):
        """Initialize the export service.

        Args:
            workspace_path: Path to the workspace for exports.
        """
        self.workspace_path = Path(workspace_path)
        self.exports_dir = self.workspace_path / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_to_csv(
        self,
        data: list[dict],
        filename: str,
        fieldnames: list[str] | None = None,
    ) -> Path:
        """Export data to a CSV file.

        Args:
            data: List of dictionaries to export.
            filename: Name of the output file (with or without .csv).
            fieldnames: Optional list of field names (column order).

        Returns:
            Path to the created CSV file.
        """
        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"

        filepath = self.exports_dir / filename

        if not data:
            # Create empty file with headers if no data
            filepath.touch()
            return filepath

        # Determine fieldnames from data if not provided
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        return filepath

    def export_cost_estimate(
        self,
        estimate: dict,
        filename: str | None = None,
    ) -> Path:
        """Export a cost estimate to CSV.

        Args:
            estimate: ProjectEstimate dictionary with cost breakdowns.
            filename: Optional filename (auto-generated if not provided).

        Returns:
            Path to the created CSV file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_estimate_{timestamp}.csv"

        # Flatten all costs into single list
        all_costs = []

        for cost in estimate.get("material_costs", []):
            all_costs.append({**cost, "type": "Material"})

        for cost in estimate.get("labor_costs", []):
            all_costs.append({**cost, "type": "Labor"})

        for cost in estimate.get("regulatory_costs", []):
            all_costs.append({**cost, "type": "Regulatory"})

        for cost in estimate.get("other_costs", []):
            all_costs.append({**cost, "type": "Other"})

        # Add summary row
        all_costs.append({
            "type": "TOTAL",
            "category": "",
            "description": "Total Estimated Cost",
            "estimated_cost": estimate.get("total_estimated_cost", 0),
            "currency": "USD",
            "source": "",
            "confidence": "",
        })

        fieldnames = [
            "type",
            "category",
            "description",
            "estimated_cost",
            "currency",
            "source",
            "confidence",
        ]

        return self.export_to_csv(all_costs, filename, fieldnames)

    def export_document_list(
        self,
        documents: list[dict],
        filename: str | None = None,
    ) -> Path:
        """Export a list of documents to CSV.

        Args:
            documents: List of document metadata dictionaries.
            filename: Optional filename.

        Returns:
            Path to the created CSV file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_list_{timestamp}.csv"

        fieldnames = [
            "document_type",
            "title",
            "file_path",
            "created_by_agent",
            "created_at",
        ]

        return self.export_to_csv(documents, filename, fieldnames)

    def export_agent_history(
        self,
        runs: list[dict],
        filename: str | None = None,
    ) -> Path:
        """Export agent run history to CSV.

        Args:
            runs: List of agent run records.
            filename: Optional filename.

        Returns:
            Path to the created CSV file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_history_{timestamp}.csv"

        fieldnames = [
            "id",
            "agent_type",
            "status",
            "started_at",
            "completed_at",
            "prompt",
        ]

        return self.export_to_csv(runs, filename, fieldnames)

    def export_to_markdown(
        self,
        content: str,
        filename: str,
        metadata: dict | None = None,
    ) -> Path:
        """Export content to a Markdown file.

        Args:
            content: Markdown content.
            filename: Name of the output file.
            metadata: Optional YAML frontmatter metadata.

        Returns:
            Path to the created file.
        """
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        filepath = self.exports_dir / filename

        # Build file content
        file_content = ""

        if metadata:
            file_content = "---\n"
            for key, value in metadata.items():
                file_content += f"{key}: {value}\n"
            file_content += "---\n\n"

        file_content += content

        filepath.write_text(file_content, encoding="utf-8")
        return filepath

    def list_exports(self) -> list[dict]:
        """List all files in the exports directory.

        Returns:
            List of export file info dictionaries.
        """
        exports = []

        for file_path in self.exports_dir.iterdir():
            if file_path.is_file():
                exports.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                    "type": file_path.suffix.lower(),
                })

        return sorted(exports, key=lambda x: x["modified"], reverse=True)
