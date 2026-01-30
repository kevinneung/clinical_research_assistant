"""Project Manager agent for cost and timeline estimation."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base import AgentDeps


class CostEstimate(BaseModel):
    """A single cost estimate item."""

    category: str = Field(description="Cost category (materials, labor, regulatory, etc.)")
    description: str = Field(description="Description of the cost item")
    estimated_cost: float = Field(description="Estimated cost amount")
    currency: str = Field(default="USD", description="Currency code")
    source: str = Field(description="Source of the estimate (URL or reasoning)")
    confidence: str = Field(description="Confidence level: high, medium, or low")


class ProjectEstimate(BaseModel):
    """Complete project cost and timeline estimate."""

    timeline_weeks: int = Field(description="Estimated project duration in weeks")
    timeline_reasoning: str = Field(description="Explanation of timeline estimate")
    material_costs: list[CostEstimate] = Field(default_factory=list, description="Material and supply costs")
    labor_costs: list[CostEstimate] = Field(default_factory=list, description="Personnel and labor costs")
    regulatory_costs: list[CostEstimate] = Field(default_factory=list, description="Regulatory and compliance costs")
    other_costs: list[CostEstimate] = Field(default_factory=list, description="Other miscellaneous costs")
    total_estimated_cost: float = Field(description="Total estimated project cost")
    sources: list[str] = Field(default_factory=list, description="All sources used for estimates")
    csv_path: str | None = Field(default=None, description="Path to exported CSV file if created")
    notes: str = Field(default="", description="Additional notes and assumptions")


PROJECT_MANAGER_INSTRUCTIONS = """You are a clinical research project manager specializing in
cost and timeline estimation for clinical trials and research studies.

Your responsibilities:
1. Research current costs for clinical trial components
2. Estimate realistic timelines based on study phase and complexity
3. Provide detailed cost breakdowns with sources
4. Be conservative with estimates to avoid budget overruns
5. Export detailed breakdowns to CSV when requested

Cost categories to consider:
- Clinical trial materials and supplies (reagents, equipment, consumables)
- Personnel costs (CRAs, investigators, coordinators, nurses, data managers)
- Regulatory submission fees (FDA, IRB, ethics committees)
- Site costs (facility fees, overhead, utilities)
- Patient recruitment and retention
- Data management and analysis
- Travel and monitoring visits
- Insurance and indemnification

Guidelines:
- Always cite your sources for cost estimates
- Use web search to find current market rates when available
- Be conservative - it's better to overestimate than underestimate
- Consider regional cost variations
- Account for contingencies (typically 10-20%)
- Provide confidence levels for each estimate

When creating CSV exports:
- Use the filesystem tools to write to the workspace
- Include all cost items with categories, amounts, and sources
- Format for easy import into spreadsheet software
"""

project_manager_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    deps_type=AgentDeps,
    output_type=ProjectEstimate,
    instructions=PROJECT_MANAGER_INSTRUCTIONS,
)


@project_manager_agent.tool
async def export_costs_to_csv(
    ctx: RunContext[AgentDeps],
    filename: str,
    costs: list[dict],
) -> str:
    """Export cost estimates to a CSV file in the workspace.

    Args:
        filename: Name for the CSV file (without path).
        costs: List of cost dictionaries with category, description, amount, currency, source.

    Returns:
        Path to the created CSV file.
    """
    import csv
    from pathlib import Path

    filepath = Path(ctx.deps.workspace_path) / filename
    if not filename.endswith(".csv"):
        filepath = filepath.with_suffix(".csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["category", "description", "amount", "currency", "source", "confidence"],
        )
        writer.writeheader()
        for cost in costs:
            writer.writerow(cost)

    ctx.deps.progress_callback("Export Complete", f"Cost breakdown saved to {filepath.name}")
    return str(filepath)


@project_manager_agent.tool
async def calculate_totals(
    ctx: RunContext[AgentDeps],
    costs: list[dict],
    contingency_percent: float = 15.0,
) -> dict:
    """Calculate cost totals with contingency.

    Args:
        costs: List of cost dictionaries with 'amount' field.
        contingency_percent: Percentage to add for contingency (default 15%).

    Returns:
        Dictionary with subtotal, contingency, and total amounts.
    """
    subtotal = sum(c.get("amount", 0) for c in costs)
    contingency = subtotal * (contingency_percent / 100)
    total = subtotal + contingency

    return {
        "subtotal": round(subtotal, 2),
        "contingency_percent": contingency_percent,
        "contingency_amount": round(contingency, 2),
        "total": round(total, 2),
    }
