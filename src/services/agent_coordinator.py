"""Agent coordinator service for managing agent execution."""

import asyncio
import traceback
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot, QThread
from sqlalchemy.orm import Session

from src.agents import orchestrator_agent, AgentDeps
from src.mcp import create_mcp_toolsets, MCPToolsets
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


def _is_mcp_error(exc: BaseException) -> bool:
    """Check whether an exception was caused by MCP server startup failure.

    Recursively inspects ExceptionGroups for known MCP-related errors
    (TimeoutError, FileNotFoundError, ConnectionError, OSError).
    """
    mcp_types = (TimeoutError, FileNotFoundError, ConnectionError, OSError)
    if isinstance(exc, mcp_types):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(_is_mcp_error(sub) for sub in exc.exceptions)
    if exc.__cause__ is not None:
        return _is_mcp_error(exc.__cause__)
    return False


def _format_user_error(error: str) -> str:
    """Map known error patterns to user-friendly messages."""
    lower = error.lower()
    if "npx" in lower and ("not found" in lower or "no such file" in lower):
        return (
            "Node.js (npx) is not installed or not on your PATH.\n"
            "Install it from https://nodejs.org to enable MCP tools.\n"
            "Agents will still work without tool access."
        )
    if "timeout" in lower or "timedout" in lower:
        return (
            "An MCP tool server timed out while starting. This can happen on "
            "the first run while packages are downloaded.\n"
            "The request will be retried without tools. You can try again later "
            "once the packages are cached."
        )
    if "api_key" in lower or "authentication" in lower or "401" in lower:
        return (
            "API authentication failed. Please check that your ANTHROPIC_API_KEY "
            "is set correctly in your .env file."
        )
    return error


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
    question_asked = Signal(str, list)  # question text, options list
    plan_updated = Signal(dict)  # plan data
    step_status_changed = Signal(int, str)  # step_index, status
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
        self._question_event: asyncio.Event | None = None
        self._question_answer: str = ""
        self._current_worker: AgentWorker | None = None
        self._mcp_toolsets = None
        self._pending_plan: dict | None = None
        self._executing_plan: dict | None = None
        self._current_step_index: int = -1

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
            self._mcp_toolsets = create_mcp_toolsets(
                self.project.workspace_path,
                npx_available=get_config().npx_available,
            )

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
                question_callback=self._ask_question,
            )

            # Run agent with MCP servers passed as toolsets
            mcp_servers = deps.get_active_mcp_servers()

            try:
                result = await orchestrator_agent.run(
                    prompt,
                    deps=deps,
                    model=get_config().default_model,
                    toolsets=mcp_servers,
                )
            except BaseException as mcp_exc:
                if mcp_servers and _is_mcp_error(mcp_exc):
                    # MCP server failed — notify user and retry without tools
                    self._send_progress(
                        "MCP Unavailable",
                        "Tool servers failed to start. Retrying without tools...",
                    )
                    self._mcp_toolsets = MCPToolsets()
                    result = await orchestrator_agent.run(
                        prompt,
                        deps=deps,
                        model=get_config().default_model,
                    )
                else:
                    raise

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

        # Track step progress during plan execution
        if status == "Delegating" and self._executing_plan:
            steps = self._executing_plan.get("steps", [])
            # Mark previous step as completed
            if 0 <= self._current_step_index < len(steps):
                self.step_status_changed.emit(self._current_step_index, "completed")
            # Advance to next step and mark it running
            self._current_step_index += 1
            if self._current_step_index < len(steps):
                self.step_status_changed.emit(self._current_step_index, "running")

    async def _ask_question(self, question: str, options: list[str]) -> str:
        """Ask the researcher a multiple-choice question via the UI.

        Args:
            question: The question text.
            options: List of answer choices.

        Returns:
            The researcher's answer string.
        """
        self._question_event = asyncio.Event()
        self._question_answer = ""

        # Emit signal to UI (received on main thread)
        self.question_asked.emit(question, options)
        self.status_changed.emit("waiting", "Your response")

        # Wait for response
        await self._question_event.wait()

        self.status_changed.emit("running", "Orchestrator")
        return self._question_answer

    @Slot(str)
    def handle_question_response(self, answer: str) -> None:
        """Handle the researcher's answer from the UI.

        Args:
            answer: The selected or typed answer.
        """
        self._question_answer = answer
        if self._question_event and self._current_worker and self._current_worker.loop:
            self._current_worker.loop.call_soon_threadsafe(
                self._question_event.set
            )

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
            # Mark all plan steps as completed
            if self._executing_plan:
                for i in range(len(self._executing_plan.get("steps", []))):
                    self.step_status_changed.emit(i, "completed")
                self._executing_plan = None
                self._current_step_index = -1
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
        # Mark current step as failed during plan execution
        if self._executing_plan:
            if 0 <= self._current_step_index < len(self._executing_plan.get("steps", [])):
                self.step_status_changed.emit(self._current_step_index, "failed")
            self._executing_plan = None
            self._current_step_index = -1
        friendly = _format_user_error(error)
        self.status_changed.emit("error", "")
        self.task_changed.emit("")
        self.message_received.emit("System", f"Error: {friendly}")
        self.history_entry.emit("Orchestrator", f"Error: {friendly}", "failed")

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

        self._executing_plan = plan_data
        self._current_step_index = -1
        self.run_async(execution_prompt)

    def stop(self) -> None:
        """Stop the current agent execution."""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
            self._current_worker = None
            self.status_changed.emit("idle", "")
            self.task_changed.emit("")
