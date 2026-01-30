"""Main application entry point for the Clinical Research Assistant."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from src.utils.config import load_config
from src.utils.logging import setup_logging, get_logger
from src.models import init_db, get_session, Project
from src.services import AgentCoordinator, WorkspaceManager
from src.ui import MainWindow


def create_or_load_project(db_session, workspace_manager: WorkspaceManager) -> Project:
    """Create a new project or load the most recent one.

    Args:
        db_session: Database session.
        workspace_manager: Workspace manager instance.

    Returns:
        Project instance.
    """
    # Check for existing projects
    existing = db_session.query(Project).order_by(Project.updated_at.desc()).first()

    if existing:
        # Verify workspace exists
        if Path(existing.workspace_path).exists():
            return existing

    # Create new default project
    workspace_path = workspace_manager.create_workspace("Default_Project")

    project = Project(
        name="Default Project",
        description="Default clinical research project",
        workspace_path=str(workspace_path),
    )
    db_session.add(project)
    db_session.commit()

    return project


def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(
        level=config.log_level,
        log_file=config.log_file,
    )
    logger = get_logger(__name__)

    # Validate configuration
    errors = config.validate()
    if errors:
        logger.warning(f"Configuration warnings: {errors}")

    # Initialize database
    logger.info("Initializing database...")
    init_db(config.database_path)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Clinical Research Assistant")
    app.setOrganizationName("CRA")
    app.setOrganizationDomain("clinical-research-assistant.local")

    # Get database session
    session_gen = get_session()
    db_session = next(session_gen)

    try:
        # Initialize workspace manager
        workspace_manager = WorkspaceManager(config.workspaces_dir)

        # Create or load project
        logger.info("Loading project...")
        project = create_or_load_project(db_session, workspace_manager)
        logger.info(f"Using project: {project.name} at {project.workspace_path}")

        # Create agent coordinator
        coordinator = AgentCoordinator(db_session, project)

        # Create and show main window
        logger.info("Starting UI...")
        window = MainWindow(coordinator)

        # Connect coordinator signals to UI
        coordinator.status_changed.connect(
            lambda status, agent: window.status_panel.set_status(status, agent)
        )
        coordinator.task_changed.connect(window.status_panel.set_current_task)
        coordinator.history_entry.connect(window.status_panel.add_history_entry)

        # Set initial workspace in UI
        window.workspace_panel.set_workspace(project.workspace_path)

        window.show()

        # Show welcome message
        window.chat_panel.append_message(
            "Assistant",
            "Welcome to the Clinical Research Assistant. "
            "I can help you plan clinical trials, estimate costs, "
            "draft compliance documents, and more. How can I help you today?"
        )

        # Check for API key
        if not config.anthropic_api_key:
            QMessageBox.warning(
                window,
                "API Key Missing",
                "ANTHROPIC_API_KEY is not set. Please set this environment variable "
                "to enable AI functionality.\n\n"
                "You can still explore the interface, but agent features will not work."
            )

        # Run application
        exit_code = app.exec()

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
    finally:
        # Clean up
        try:
            next(session_gen)
        except StopIteration:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
