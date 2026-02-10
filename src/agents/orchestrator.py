"""Main orchestrator agent for coordinating clinical research workflows."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base import AgentDeps
from src.utils.config import get_config


class PlanStep(BaseModel):
    """A single step in the execution plan."""

    description: str = Field(description="What this step accomplishes")
    agent: str = Field(description="Agent to handle this step: project_manager, document_maker, or email_drafter")
    requires_approval: bool = Field(description="Whether human approval is needed before executing")
    inputs: dict[str, str] = Field(default_factory=dict, description="Input parameters for the agent")


class TaskPlan(BaseModel):
    """Structured plan for researcher review."""

    goal: str = Field(description="The overall goal of this task")
    steps: list[PlanStep] = Field(description="Ordered list of steps to accomplish the goal")
    estimated_agents: list[str] = Field(description="List of agents that will be involved")


ORCHESTRATOR_INSTRUCTIONS = """You are a clinical research orchestrator helping researchers
plan and execute study workflows. Your role is to:

1. Understand the researcher's request and break it down into actionable steps
2. Create detailed execution plans that identify which specialized agent handles each step
3. Delegate tasks to the appropriate downstream agents
4. Keep the researcher informed of progress
5. Request human approval before any irreversible actions

Available downstream agents:
- project_manager: Handles cost estimation, timeline planning, resource allocation, and budget analysis
- document_maker: Creates compliance documents (ICF, protocols, IRB applications, etc.)
- email_drafter: Drafts professional emails for various stakeholders

Guidelines:
- Always break down complex requests into specific, actionable steps
- Identify which downstream agent should handle each step
- Use the filesystem tools to read/write documents in the workspace
- Request human approval before sending emails or finalizing important documents
- Provide clear progress updates to keep the researcher informed

When using MCP tools:
- Use filesystem tools to read existing documents and write new ones
- Use web search (if available) to research costs, regulations, and best practices
"""

orchestrator_agent = Agent(
    deps_type=AgentDeps,
    output_type=TaskPlan | str,
    instructions=ORCHESTRATOR_INSTRUCTIONS,
)


@orchestrator_agent.tool
async def delegate_to_project_manager(
    ctx: RunContext[AgentDeps],
    task: str,
    research_queries: list[str] | None = None,
) -> str:
    """Delegate cost/timeline estimation to the Project Manager agent.

    Args:
        task: Description of the estimation task.
        research_queries: Optional list of specific items to research costs for.

    Returns:
        The project manager's response with cost and timeline estimates.
    """
    from .project_manager import project_manager_agent

    ctx.deps.progress_callback("Delegating", f"Project Manager: {task}")

    prompt = task
    if research_queries:
        prompt += f"\n\nSpecific items to research: {', '.join(research_queries)}"

    result = await project_manager_agent.run(
        prompt, deps=ctx.deps, model=get_config().default_model
    )

    return str(result.output)


@orchestrator_agent.tool
async def delegate_to_document_maker(
    ctx: RunContext[AgentDeps],
    document_type: str,
    context: str,
) -> str:
    """Delegate document drafting to the Document Maker agent.

    Args:
        document_type: Type of document (ICF, Protocol, IB, IRB Application, etc.)
        context: Background information and requirements for the document.

    Returns:
        The document maker's response with document details and file path.
    """
    from .document_maker import document_maker_agent

    ctx.deps.progress_callback("Delegating", f"Document Maker: Creating {document_type}")

    prompt = f"Create a {document_type} document.\n\nContext: {context}"

    result = await document_maker_agent.run(
        prompt, deps=ctx.deps, model=get_config().default_model
    )

    return str(result.output)


@orchestrator_agent.tool
async def delegate_to_email_drafter(
    ctx: RunContext[AgentDeps],
    email_purpose: str,
    recipients: list[str],
    context: str,
) -> str:
    """Delegate email drafting to the Email Drafter agent.

    Args:
        email_purpose: Purpose of the email (compliance, team_update, recruitment, etc.)
        recipients: List of recipient roles or names.
        context: Background information for the email content.

    Returns:
        The email drafter's response with the draft email.
    """
    from .email_drafter import email_drafter_agent

    ctx.deps.progress_callback("Delegating", f"Email Drafter: {email_purpose}")

    prompt = f"Draft an email for {email_purpose}.\n\nRecipients: {', '.join(recipients)}\n\nContext: {context}"

    result = await email_drafter_agent.run(
        prompt, deps=ctx.deps, model=get_config().default_model
    )

    return str(result.output)


@orchestrator_agent.tool
async def request_researcher_approval(
    ctx: RunContext[AgentDeps],
    action_description: str,
    details: dict,
) -> bool:
    """Request human approval before proceeding with an action.

    Args:
        action_description: Brief description of the proposed action.
        details: Dictionary with detailed information about the action.

    Returns:
        True if approved, False if denied.
    """
    ctx.deps.progress_callback("Approval Required", action_description)
    return await ctx.deps.approval_callback(action_description, details)


@orchestrator_agent.tool
async def update_researcher(
    ctx: RunContext[AgentDeps],
    status: str,
    details: str,
) -> None:
    """Send a progress update to the researcher.

    Args:
        status: Brief status label (e.g., "In Progress", "Completed").
        details: Detailed description of current progress.
    """
    ctx.deps.progress_callback(status, details)
