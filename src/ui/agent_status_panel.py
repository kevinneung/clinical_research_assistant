"""Agent status and history panel."""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QFrame,
)
from PySide6.QtCore import Slot, Qt


class AgentStatusPanel(QWidget):
    """Panel showing agent execution status and history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the status panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QLabel("Agent Status")
        header.setObjectName("header")
        layout.addWidget(header)

        # Current status
        status_group = QGroupBox("Current Activity")
        status_layout = QVBoxLayout(status_group)

        self.status_indicator = QLabel("● Idle")
        self.status_indicator.setStyleSheet("color: #9E9E9E; font-weight: bold;")
        status_layout.addWidget(self.status_indicator)

        self.current_agent_label = QLabel("No active agent")
        self.current_agent_label.setStyleSheet("color: #666666;")
        status_layout.addWidget(self.current_agent_label)

        self.current_task_label = QLabel("")
        self.current_task_label.setWordWrap(True)
        self.current_task_label.setStyleSheet("color: #333333; font-size: 12px;")
        status_layout.addWidget(self.current_task_label)

        layout.addWidget(status_group)

        # Active agents
        agents_group = QGroupBox("Agents")
        agents_layout = QVBoxLayout(agents_group)

        self.agents_list = QListWidget()
        self.agents_list.setMaximumHeight(120)

        # Add default agents
        agents = [
            ("Orchestrator", "Coordinates workflows"),
            ("Project Manager", "Cost & timeline estimation"),
            ("Document Maker", "Compliance documents"),
            ("Email Drafter", "Professional correspondence"),
        ]

        for name, desc in agents:
            item = QListWidgetItem(f"{name}")
            item.setToolTip(desc)
            self.agents_list.addItem(item)

        agents_layout.addWidget(self.agents_list)
        layout.addWidget(agents_group)

        # History
        history_group = QGroupBox("Recent Activity")
        history_layout = QVBoxLayout(history_group)

        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)

        layout.addWidget(history_group)

    @Slot(str, str)
    def set_status(self, status: str, agent: str = "") -> None:
        """Update the current status display.

        Args:
            status: Status message (idle, running, completed, error).
            agent: Name of the active agent.
        """
        status_colors = {
            "idle": "#9E9E9E",
            "running": "#2196F3",
            "completed": "#4CAF50",
            "error": "#f44336",
            "waiting": "#FF9800",
        }

        color = status_colors.get(status.lower(), "#9E9E9E")
        self.status_indicator.setText(f"● {status.title()}")
        self.status_indicator.setStyleSheet(f"color: {color}; font-weight: bold;")

        if agent:
            self.current_agent_label.setText(f"Agent: {agent}")
        else:
            self.current_agent_label.setText("No active agent")

    @Slot(str)
    def set_current_task(self, task: str) -> None:
        """Update the current task description.

        Args:
            task: Description of the current task.
        """
        self.current_task_label.setText(task)

    @Slot(str, str, str)
    def add_history_entry(self, agent: str, action: str, status: str = "completed") -> None:
        """Add an entry to the history list.

        Args:
            agent: Name of the agent.
            action: Description of the action.
            status: Status of the action (completed, failed).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        status_icons = {
            "completed": "✓",
            "failed": "✗",
            "running": "→",
            "pending": "○",
        }
        icon = status_icons.get(status, "•")

        item = QListWidgetItem(f"{timestamp} {icon} [{agent}] {action}")

        # Color based on status
        if status == "failed":
            item.setForeground(Qt.red)
        elif status == "completed":
            item.setForeground(Qt.darkGreen)

        self.history_list.insertItem(0, item)

        # Keep history limited
        while self.history_list.count() > 50:
            self.history_list.takeItem(self.history_list.count() - 1)

    def highlight_agent(self, agent_name: str) -> None:
        """Highlight an agent in the agents list.

        Args:
            agent_name: Name of the agent to highlight.
        """
        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            if agent_name.lower() in item.text().lower():
                item.setSelected(True)
            else:
                item.setSelected(False)

    def clear_history(self) -> None:
        """Clear the history list."""
        self.history_list.clear()

    def reset(self) -> None:
        """Reset the panel to idle state."""
        self.set_status("idle")
        self.current_task_label.setText("")
        self.agents_list.clearSelection()
