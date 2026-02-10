"""Agent coordinator service for managing agent execution."""

import asyncio
import traceback
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot, QThread
from sqlalchemy.orm import Session

from src.agents import orchestrator_agent, AgentDeps
from src.mcp import create_mcp_toolsets
from src.models import AgentRun, Approval
from src.utils.config import get_config


def _format_error(exc: BaseException) -> str:
    """Format an exception into a descriptive error string.

    Unwraps ExceptionGroups so the real causes are visible.
    """
    if isinstance(exc, BaseExceptionGroup):
        parts = [f"{type(exc).__name__}: {exc}"]
        for i, sub in enumerate(exc.exceptions, 1):
            tb = "".join(traceback.format_exception(type(sub), sub, sub.__traceback__))
            parts.append(f"\n--- Sub-exception {i} ---\n{tb}")
        return "\n".join(parts)
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def _format_plan_message(plan_data: dict) -> str:
    """Format a TaskPlan dict into a readable chat message."""
    goal = plan_data.get("goal", "No goal specified")
    steps = plan_data.get("steps", [])
    agents = plan_data.get("estimated_agents", [])

    lines = [f"<b>Plan: {goal}</b><br>"]
    for i, step in enumerate(steps, 1):
        agent = step.get("agent", "unknown")
        desc = step.get("description", "")
        approval = " ⚠ <i>requires approval</i>" if step.get("requires_approval") else ""
        lines.append(f"{i}. [{agent}] {desc}{approval}")

    if agents:
        lines.append(f"<br><b>Agents involved:</b> {', '.join(agents)}")

    return "<br>".join(lines)


class AgentWorker(QThread):
    """Worker thread for running agents asynchronously."""

    finished = Signal(object)  # Result or error
    error = Signal(str)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self.loop: asyncio.AbstractEventLoop | None = None

    def run(self):
        """Run the coroutine in a new event loop."""
        try:
            result = asyncio.run(self.coro)
            self.finished.emit(result)
        except BaseException as e:
            self.error.emit(_format_error(e))


class AgentCoordinator(QObject):
    """Coordinates agent execution with UI updates.

    This class bridges the async agent execution with the Qt event loop,
    handling signals between the UI and the Pydantic-AI agents.
    """

    # Signals for UI updates
    message_received = Signal(str, str)  # sender, content
    approval_requested = Signal(str, dict)  # action, details
    plan_updated = Signal(dict)  # plan data
    status_changed = Signal(str, str)  # status, agent
    task_changed = Signal(str)  # task description
    history_entry = Signal(str, str, str)  # agent, action, status

    def __init__(self, db_session: Session, project):
        super().__init__()
        self.db_session = db_session
        self.project = project
        self._approval_event: asyncio.Event | None = None
        self._approval_result = False
        self._approval_notes = ""
        self._current_worker: AgentWorker | None = None
        self._mcp_toolsets = None
        self._pending_plan: dict | None = None

    def run_async(self, prompt: str) -> None:
        """Run the orchestrator agent with the given prompt.

        This method starts the agent in a background thread and returns
        immediately. Results are delivered via signals.

        Args:
            prompt: The user's prompt to process.
        """
        if self._current_worker and self._current_worker.isRunning():
            self.message_received.emit("System", "An agent is already running. Please wait.")
            return

        # Create the coroutine
        coro = self._run_orchestrator(prompt)

        # Create and start worker thread
        self._current_worker = AgentWorker(coro)
        self._current_worker.finished.connect(self._on_agent_finished)
        self._current_worker.error.connect(self._on_agent_error)
        self._current_worker.start()

        self.status_changed.emit("running", "Orchestrator")
        self.task_changed.emit(prompt[:100] + "..." if len(prompt) > 100 else prompt)

    async def _run_orchestrator(self, prompt: str) -> Any:
        """Run the orchestrator agent with the given prompt.

        Args:
            prompt: The user's prompt to process.

        Returns:
            The agent's result.
        """
        # Store reference to the running loop for cross-thread approval signaling
        if self._current_worker:
            self._current_worker.loop = asyncio.get_running_loop()

        # Initialize MCP toolsets
        if self._mcp_toolsets is None:
            self._mcp_toolsets = create_mcp_toolsets(self.project.workspace_path)

        # Create agent run record
        agent_run = AgentRun(
            project_id=self.project.id,
            agent_type="orchestrator",
            prompt=prompt,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db_session.add(agent_run)
        self.db_session.commit()

        try:
            deps = AgentDeps(
                db_session=self.db_session,
                workspace_path=self.project.workspace_path,
                project_id=self.project.id,
                mcp_filesystem=self._mcp_toolsets.filesystem,
                mcp_web_search=self._mcp_toolsets.web_search,
                mcp_email=self._mcp_toolsets.email,
                approval_callback=self._request_approval,
                progress_callback=self._send_progress,
            )

            # Run agent with MCP servers passed as toolsets
            mcp_servers = deps.get_active_mcp_servers()

            result = await orchestrator_agent.run(
                prompt,
                deps=deps,
                model=get_config().default_model,
                toolsets=mcp_servers,
            )

            # Update agent run record
            agent_run.complete(
                result.output.model_dump()
                if hasattr(result.output, "model_dump")
                else str(result.output)
            )
            usage = result.usage()
            if usage:
                agent_run.token_usage = {
                    "request_tokens": usage.request_tokens,
                    "response_tokens": usage.response_tokens,
                    "total_tokens": usage.total_tokens,
                }
            self.db_session.commit()

            return result

        except Exception as e:
            agent_run.fail(str(e))
            self.db_session.commit()
            raise

    async def _request_approval(self, action: str, details: dict) -> bool:
        """Request human approval via UI signal.

        Args:
            action: Description of the action requiring approval.
            details: Additional details about the action.

        Returns:
            True if approved, False if denied.
        """
        # Create approval record
        # Note: This requires access to the current agent run
        self._approval_event = asyncio.Event()
        self._approval_result = False

        # Emit signal to UI (will be received on main thread)
        self.approval_requested.emit(action, details)
        self.status_changed.emit("waiting", "Approval")

        # Wait for response
        await self._approval_event.wait()

        self.status_changed.emit("running", "Orchestrator")
        return self._approval_result

    def _send_progress(self, status: str, details: str) -> None:
        """Send progress update to UI.

        Args:
            status: Status label.
            details: Progress details.
        """
        self.message_received.emit("Assistant", f"**{status}**: {details}")
        self.history_entry.emit("Orchestrator", f"{status}: {details}", "running")

    @Slot(bool, str)
    def handle_approval_response(self, approved: bool, notes: str = "") -> None:
        """Handle approval response from UI.

        Args:
            approved: Whether the action was approved.
            notes: Optional notes from the researcher.
        """
        self._approval_result = approved
        self._approval_notes = notes

        # If there's a pending plan awaiting execution approval
        if self._pending_plan is not None:
            plan = self._pending_plan
            self._pending_plan = None
            if approved:
                self.message_received.emit("System", "Plan approved. Executing...")
                self._execute_plan(plan, notes)
            else:
                self.message_received.emit("System", "Plan declined.")
                self.status_changed.emit("completed", "")
                self.task_changed.emit("")
            return

        # Otherwise it's an in-agent approval — wake up the waiting coroutine
        if self._approval_event:
            if self._current_worker and self._current_worker.loop:
                self._current_worker.loop.call_soon_threadsafe(
                    self._approval_event.set
                )

    @Slot(object)
    def _on_agent_finished(self, result: Any) -> None:
        """Handle agent completion.

        Args:
            result: The agent's result.
        """
        if not hasattr(result, "output"):
            self.status_changed.emit("completed", "")
            self.task_changed.emit("")
            self.history_entry.emit("Orchestrator", "Task completed", "completed")
            return

        output = result.output
        if hasattr(output, "model_dump"):
            # It's a Pydantic model (TaskPlan) — show it and ask to execute
            plan_data = output.model_dump()
            self._pending_plan = plan_data
            self.plan_updated.emit(plan_data)
            self.message_received.emit(
                "Assistant", _format_plan_message(plan_data)
            )
            self.history_entry.emit("Orchestrator", "Plan created", "completed")

            # Ask user whether to execute the plan
            self.approval_requested.emit(
                "Execute this plan?",
                {"goal": plan_data.get("goal", ""),
                 "steps": len(plan_data.get("steps", []))},
            )
        else:
            # Plain string result (execution summary) — just display it
            self.status_changed.emit("completed", "")
            self.task_changed.emit("")
            self.message_received.emit("Assistant", str(output))
            self.history_entry.emit("Orchestrator", "Task completed", "completed")

    @Slot(str)
    def _on_agent_error(self, error: str) -> None:
        """Handle agent error.

        Args:
            error: Error message.
        """
        self.status_changed.emit("error", "")
        self.task_changed.emit("")
        self.message_received.emit("System", f"Error: {error}")
        self.history_entry.emit("Orchestrator", f"Error: {error}", "failed")

    def _execute_plan(self, plan_data: dict, notes: str = "") -> None:
        """Run the orchestrator again to execute an approved plan.

        Args:
            plan_data: The approved TaskPlan dict.
            notes: Optional notes from the researcher.
        """
        steps_text = "\n".join(
            f"  {i}. [{s.get('agent')}] {s.get('description')}"
            for i, s in enumerate(plan_data.get("steps", []), 1)
        )
        execution_prompt = (
            f"The researcher approved the following plan. Execute it now by "
            f"delegating each step to the appropriate agent using your tools. "
            f"Do NOT return another plan — use delegate_to_project_manager, "
            f"delegate_to_document_maker, and delegate_to_email_drafter to "
            f"actually perform each step. Report results as a text summary.\n\n"
            f"Goal: {plan_data.get('goal', '')}\n"
            f"Steps:\n{steps_text}"
        )
        if notes:
            execution_prompt += f"\n\nResearcher notes: {notes}"

        self.run_async(execution_prompt)

    def stop(self) -> None:
        """Stop the current agent execution."""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
            self._current_worker = None
            self.status_changed.emit("idle", "")
            self.task_changed.emit("")
