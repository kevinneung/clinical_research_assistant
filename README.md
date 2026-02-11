# Clinical Research Assistant

A multi-agent clinical research assistant built with **Pydantic-AI**, **PySide6**, and **SQLite** that automates labor-intensive clinical study workflows through orchestrated AI agents with human-in-the-loop approval flows.

## Features

- **Multi-Agent Architecture**: Orchestrated AI agents specialized for different clinical research tasks
  - **Orchestrator Agent**: Coordinates workflows and delegates to specialized agents
  - **Project Manager Agent**: Cost estimation, timeline planning, and resource allocation
  - **Document Maker Agent**: Compliance document drafting (ICF, protocols, IRB applications)
  - **Email Drafter Agent**: Professional correspondence for clinical research

- **Human-in-the-Loop**: Approval dialogs for critical actions before execution

- **MCP Integration**: Model Context Protocol for filesystem operations and web search

- **Desktop UI**: Full-featured PySide6 interface with:
  - Chat panel for natural language interaction
  - Workspace file browser
  - Execution plan viewer
  - Agent status monitoring

## Quick Start

### Prerequisites

- **Python 3.11+**
  - Windows: [python.org/downloads](https://www.python.org/downloads/) (check "Add Python to PATH" during install)
  - macOS: `brew install python@3.13`
  - Linux: `sudo apt install python3 python3-venv` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)
- **Node.js** (optional, enables MCP tool servers) — [nodejs.org](https://nodejs.org) or `brew install node`
- An [Anthropic API key](https://console.anthropic.com/settings/keys)

### Windows

1. Clone the repository:
   ```bash
   git clone https://github.com/kevinneung/clinical_research_assistant.git
   ```

2. Double-click **`setup.bat`** in the project folder. It will:
   - Verify your Python version
   - Create a virtual environment
   - Install all dependencies
   - Prompt you for your API key(s) and create a `.env` file
   - Offer to launch the app

3. For subsequent launches, double-click **`launch.bat`**.

> **Tip:** Right-click `launch.bat` → **Send to** → **Desktop (create shortcut)** for easy access.

### macOS / Linux

1. Clone the repository:
   ```bash
   git clone https://github.com/kevinneung/clinical_research_assistant.git
   cd clinical_research_assistant
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh launch.sh
   ./setup.sh
   ```

3. For subsequent launches:
   ```bash
   ./launch.sh
   ```

> **Tip (macOS):** Create an Automator "Application" that runs `./launch.sh` and drag it to your Dock.

### Manual Setup

If you prefer to set things up yourself:

1. Clone the repository:
   ```bash
   git clone https://github.com/kevinneung/clinical_research_assistant.git
   cd clinical_research_assistant
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Create a `.env` file in the project root (see `.env.example`):
   ```
   ANTHROPIC_API_KEY=your-api-key
   BRAVE_API_KEY=your-brave-api-key   # optional
   ```

4. Run the application:
   ```bash
   python -m src.main
   ```

## Usage

### Example Workflows

1. **Plan a Clinical Trial**
   > "I need to plan a Phase 2 clinical trial for a diabetes drug. Can you help me estimate costs and identify required documents?"

2. **Draft Compliance Documents**
   > "Create an Informed Consent Form for a study on hypertension treatment."

3. **Cost Estimation**
   > "Estimate the costs for a 50-patient clinical trial including personnel, materials, and regulatory fees."

4. **Email Drafting**
   > "Draft an email to the IRB submitting our protocol amendment."

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PySide6 Desktop App                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Chat Panel  │  │  Workspace   │  │   Approval Dialog    │  │
│  │  (QTextEdit) │  │  (File Tree) │  │   (Human-in-loop)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                           │
│  - Accepts researcher prompts                                   │
│  - Creates execution plans                                      │
│  - Delegates to downstream agents                               │
└─────────────────────────────────────────────────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Project Manager │ │ Document Maker  │ │  Email Drafter  │
│     Agent       │ │     Agent       │ │     Agent       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MCP Toolsets                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Filesystem │  │ Web Search  │  │   Email (optional)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
clinical_research_assistant/
├── src/
│   ├── agents/           # Pydantic-AI agent definitions
│   ├── mcp/              # MCP server configurations
│   ├── models/           # SQLAlchemy database models
│   ├── ui/               # PySide6 UI components
│   ├── services/         # Business logic services
│   └── utils/            # Configuration and logging
├── tests/                # Test suite
├── workspaces/           # User project workspaces
└── mcp_servers/          # MCP server configs
```

## Configuration

The application can be configured via environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Yes |
| `BRAVE_API_KEY` | Brave Search API key | No |
| `CRA_APP_DATA_DIR` | Application data directory | No |
| `CRA_LOG_LEVEL` | Log level (DEBUG, INFO, etc.) | No |
| `CRA_DEFAULT_MODEL` | Default AI model | No |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Code Style

The project follows standard Python conventions. Format code with:
```bash
black src tests
ruff check src tests
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.
