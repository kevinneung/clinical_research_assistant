"""Tests for the orchestrator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.base import AgentDeps
from src.agents.orchestrator import orchestrator_agent, TaskPlan, PlanStep


@pytest.fixture
def mock_deps():
    """Create mock agent dependencies."""
    deps = MagicMock(spec=AgentDeps)
    deps.db_session = MagicMock()
    deps.workspace_path = "/tmp/test_workspace"
    deps.project_id = 1
    deps.mcp_filesystem = MagicMock()
    deps.mcp_web_search = None
    deps.mcp_email = None
    deps.approval_callback = AsyncMock(return_value=True)
    deps.progress_callback = MagicMock()
    deps.get_active_mcp_servers = MagicMock(return_value=[deps.mcp_filesystem])
    return deps


class TestTaskPlan:
    """Tests for TaskPlan model."""

    def test_task_plan_creation(self):
        """Test creating a TaskPlan."""
        plan = TaskPlan(
            goal="Plan a clinical trial",
            steps=[
                PlanStep(
                    description="Research costs",
                    agent="project_manager",
                    requires_approval=False,
                    inputs={"task": "estimate costs"},
                )
            ],
            estimated_agents=["project_manager"],
        )

        assert plan.goal == "Plan a clinical trial"
        assert len(plan.steps) == 1
        assert plan.steps[0].agent == "project_manager"

    def test_plan_step_defaults(self):
        """Test PlanStep default values."""
        step = PlanStep(
            description="Test step",
            agent="orchestrator",
            requires_approval=True,
        )

        assert step.inputs == {}
        assert step.requires_approval is True


class TestOrchestratorAgent:
    """Tests for the orchestrator agent."""

    def test_agent_has_instructions(self):
        """Test that the agent has proper instructions."""
        assert orchestrator_agent._instructions is not None
        # Instructions are now a callable; verify by checking the constant
        from src.agents.orchestrator import ORCHESTRATOR_INSTRUCTIONS
        assert "clinical research" in ORCHESTRATOR_INSTRUCTIONS.lower()

    def test_agent_has_tools(self):
        """Test that the agent has the expected tools."""
        tool_names = [t.name for t in orchestrator_agent._tools]

        assert "delegate_to_project_manager" in tool_names
        assert "delegate_to_document_maker" in tool_names
        assert "delegate_to_email_drafter" in tool_names
        assert "request_researcher_approval" in tool_names
        assert "update_researcher" in tool_names


# Integration tests would go here, requiring actual API calls
# These should be marked with @pytest.mark.integration
