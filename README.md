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

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js (for MCP servers)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/clinical_research_assistant.git
   cd clinical_research_assistant
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Set up environment variables:
   ```bash
   # Required
   export ANTHROPIC_API_KEY="your-api-key"

   # Optional - for web search functionality
   export BRAVE_API_KEY="your-brave-api-key"
   ```

## Usage

### Running the Application

```bash
python -m src.main
```

Or if installed:
```bash
clinical-assistant
```

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
