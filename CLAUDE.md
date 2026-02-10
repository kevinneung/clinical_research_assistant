# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clinical Research Assistant is a multi-agent desktop application that automates clinical research workflows through specialized AI agents with human-in-the-loop approval. Built with **Pydantic-AI** (agents), **PySide6** (Qt desktop UI), **SQLAlchemy** (SQLite ORM), and **MCP** (tool integration).

## Common Commands

```bash
# Install
pip install -e .                  # Development install
pip install -e ".[dev]"           # With dev dependencies (pytest, pytest-asyncio, pytest-qt)

# Run
python -m src.main                # Launch application
clinical-assistant                # Console script entry point

# Test
pytest                            # All tests
pytest tests/test_agents/         # Agent tests only
pytest tests/test_services/       # Service tests only
pytest tests/test_ui/             # UI tests (requires pytest-qt)
pytest tests/test_agents/test_orchestrator.py -k "test_task_plan_model"  # Single test

# Code quality
black src tests                   # Format
ruff check src tests              # Lint
```

## Architecture

### Agent System (src/agents/)

An **Orchestrator** agent receives user prompts, creates a `TaskPlan`, and delegates to three specialized agents:
- **ProjectManager** — cost estimation, timelines, CSV export
- **DocumentMaker** — compliance documents (ICF, Protocol, IB, IRB)
- **EmailDrafter** — professional correspondence

All agents share `AgentDeps` (defined in `base.py`) which injects: db session, workspace path, project ID, MCP servers, and approval/progress callbacks. Agents produce Pydantic structured outputs (`TaskPlan`, `ProjectEstimate`, `ComplianceDocument`, `DraftEmail`).

### Async/Qt Bridge (src/services/agent_coordinator.py)

`AgentCoordinator` is the critical integration layer. It runs async Pydantic-AI agents in a separate `AgentWorker` QThread, communicating back to the Qt main thread via signals (`message_received`, `approval_requested`, `plan_updated`, `status_changed`). Human approval requests block the async agent via `asyncio.Event` until the user responds in the UI.

### UI Layout (src/ui/)

Three-panel PySide6 layout:
- **Left**: `WorkspacePanel` — file tree browser for project workspace
- **Center**: `ChatPanel` — message display and input
- **Right**: Split between `PlanViewer` (execution plan with step status) and `AgentStatusPanel` (active agents, history)

`ApprovalDialog` is a modal dialog triggered by agent approval requests. Styling uses Material Design colors defined in `styles.py`.

### Data Flow

User input → `ChatPanel` signal → `MainWindow` → `AgentCoordinator.run_async()` → `AgentWorker` thread → Orchestrator agent (may delegate/request approval) → signals back to UI → database persistence (`AgentRun`, `Approval` records).

### Database (src/models/)

SQLite at `~/.clinical_research_assistant/database.db`. Models: `Project`, `AgentRun` (execution tracking with start/complete/fail lifecycle), `Approval` (human decisions linked to runs), `Document` (generated file metadata). Initialized in `database.py` with `check_same_thread=False` for Qt threading.

### MCP Integration (src/mcp/)

Agents use MCP servers for tools rather than direct API calls. Filesystem MCP is always available (scoped to workspace). Brave Search MCP is optional (requires `BRAVE_API_KEY`). Email MCP is planned but not yet implemented. Config lives in `mcp_servers/mcp_config.json` with template variables.

### Services (src/services/)

- `WorkspaceManager` — file operations, workspace creation with standard subdirs (documents/, drafts/, exports/)
- `ExportService` — CSV and Markdown export with optional YAML frontmatter

## Configuration

Environment variables (loaded via python-dotenv):
- `ANTHROPIC_API_KEY` — required
- `BRAVE_API_KEY` — optional, enables web search MCP
- `CRA_APP_DATA_DIR` — default: `~/.clinical_research_assistant`
- `CRA_DEFAULT_MODEL` — default: `claude-sonnet-4-20250514`
- `CRA_LOG_LEVEL`, `CRA_LOG_FILE` — logging config

Config dataclass in `src/utils/config.py`. Logging setup in `src/utils/logging.py` with structured formatting.

## Key Patterns

- **Adding a new agent**: Define in `src/agents/`, create structured output model, add delegation tool in orchestrator, register in coordinator
- **Agent tools** follow a consistent pattern: decorated functions receiving `RunContext[AgentDeps]` for access to workspace, db, and callbacks
- **Tests** use `asyncio_mode = "auto"` (configured in pyproject.toml); UI tests require pytest-qt
- All agents use model `claude-sonnet-4-20250514` by default
