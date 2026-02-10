"""Main application window for the Clinical Research Assistant."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QStatusBar,
    QMenuBar,
    QMenu,
    QMessageBox,
    QFileDialog,
    QLabel,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog

from .chat_panel import ChatPanel
from .workspace_panel import WorkspacePanel
from .plan_viewer import PlanViewer
from .agent_status_panel import AgentStatusPanel
from .styles import get_stylesheet


class MainWindow(QMainWindow):
    """Main application window with three-panel layout."""

    def __init__(self, coordinator=None):
        super().__init__()
        self.coordinator = coordinator

        self.setWindowTitle("Clinical Research Assistant")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_stylesheet())

        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._connect_signals()

    def _setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        menu_bar = QMenuBar()

        # File menu
        file_menu = QMenu("&File", self)

        new_project_action = QAction("&New Project...", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("&Open Project...", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_project_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        menu_bar.addMenu(file_menu)

        # View menu
        view_menu = QMenu("&View", self)

        refresh_action = QAction("&Refresh Workspace", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh_workspace)
        view_menu.addAction(refresh_action)

        menu_bar.addMenu(view_menu)

        # Help menu
        help_menu = QMenu("&Help", self)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

    def _setup_central_widget(self) -> None:
        """Set up the main three-panel layout."""
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Main splitter for three panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Workspace file browser
        self.workspace_panel = WorkspacePanel()
        splitter.addWidget(self.workspace_panel)

        # Center panel: Plan viewer + Chat
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        self.plan_viewer = PlanViewer()
        self.chat_panel = ChatPanel()

        center_layout.addWidget(self.plan_viewer, stretch=1)
        center_layout.addWidget(self.chat_panel, stretch=3)

        splitter.addWidget(center_widget)

        # Right panel: Agent status and history
        self.status_panel = AgentStatusPanel()
        splitter.addWidget(self.status_panel)

        # Set initial sizes (250, 700, 250)
        splitter.setSizes([250, 700, 250])

        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        status_bar = QStatusBar()
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        self.setStatusBar(status_bar)

    def _connect_signals(self) -> None:
        """Connect UI signals to coordinator if available."""
        if self.coordinator:
            # Connect chat panel to coordinator
            self.chat_panel.message_sent.connect(self._on_message_sent)

            # Connect coordinator signals to UI
            self.coordinator.message_received.connect(self.chat_panel.append_message)
            self.coordinator.approval_requested.connect(self._on_approval_requested)
            self.coordinator.plan_updated.connect(self.plan_viewer.update_plan)
            self.coordinator.status_changed.connect(self._on_status_changed)

    @Slot()
    def _on_new_project(self) -> None:
        """Handle new project creation."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Workspace Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.workspace_panel.set_workspace(folder)
            self.status_label.setText(f"Project: {folder}")

    @Slot()
    def _on_open_project(self) -> None:
        """Handle opening existing project."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Project Workspace",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.workspace_panel.set_workspace(folder)
            self.status_label.setText(f"Project: {folder}")

    @Slot()
    def _on_refresh_workspace(self) -> None:
        """Refresh the workspace file tree."""
        self.workspace_panel.refresh()

    @Slot()
    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Clinical Research Assistant",
            "Clinical Research Assistant v0.1.0\n\n"
            "A multi-agent system for automating clinical research workflows.\n\n"
            "Built with Pydantic-AI, PySide6, and SQLite.",
        )

    @Slot(str)
    def _on_message_sent(self, message: str) -> None:
        """Handle message sent from chat panel."""
        if self.coordinator:
            self.status_label.setText("Processing...")
            self.chat_panel.set_input_enabled(False)
            self.coordinator.run_async(message)

    @Slot(str, str)
    def _on_status_changed(self, status: str, agent: str) -> None:
        """Handle coordinator status changes to keep UI in sync."""
        status_messages = {
            "running": f"Agent working: {agent}" if agent else "Processing...",
            "waiting": "Waiting for approval...",
            "completed": "Ready",
            "error": "Error occurred",
        }
        self.status_label.setText(status_messages.get(status, "Ready"))

        if status in ("completed", "error"):
            self.chat_panel.set_input_enabled(True)

    @Slot(str, dict)
    def _on_approval_requested(self, action: str, details: dict) -> None:
        """Handle approval request from agent."""
        from .approval_dialog import ApprovalDialog

        dialog = ApprovalDialog(action, details, self)
        result = dialog.exec()

        if self.coordinator:
            approved = result == QDialog.Accepted
            notes = dialog.get_notes()
            self.coordinator.handle_approval_response(approved, notes)

    def set_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_label.setText(message)
