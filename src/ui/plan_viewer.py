"""Plan viewer widget for displaying execution plans."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QScrollArea,
    QFrame,
    QHBoxLayout,
)
from PySide6.QtCore import Slot, Qt


class PlanStepWidget(QFrame):
    """Widget for displaying a single plan step."""

    def __init__(self, step_num: int, step_data: dict, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Step header with number and agent
        header_layout = QHBoxLayout()

        step_label = QLabel(f"Step {step_num}")
        step_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        header_layout.addWidget(step_label)

        agent = step_data.get("agent", "unknown")
        agent_label = QLabel(f"[{agent}]")
        agent_label.setStyleSheet("color: #666666; font-size: 11px;")
        header_layout.addWidget(agent_label)

        if step_data.get("requires_approval"):
            approval_label = QLabel("Requires Approval")
            approval_label.setStyleSheet(
                "color: #f44336; font-size: 11px; font-weight: bold;"
            )
            header_layout.addWidget(approval_label)

        header_layout.addStretch()

        # Status indicator
        status = step_data.get("status", "pending")
        status_colors = {
            "pending": "#9E9E9E",
            "running": "#2196F3",
            "completed": "#4CAF50",
            "failed": "#f44336",
        }
        status_label = QLabel(f"● {status.title()}")
        status_label.setStyleSheet(f"color: {status_colors.get(status, '#9E9E9E')};")
        header_layout.addWidget(status_label)

        layout.addLayout(header_layout)

        # Description
        description = step_data.get("description", "No description")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #333333;")
        layout.addWidget(desc_label)


class PlanViewer(QWidget):
    """Widget for displaying the current execution plan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_plan = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the plan viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QLabel("Execution Plan")
        header.setObjectName("header")
        layout.addWidget(header)

        # Goal display
        self.goal_label = QLabel("No active plan")
        self.goal_label.setWordWrap(True)
        self.goal_label.setStyleSheet(
            "background-color: #E3F2FD; padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(self.goal_label)

        # Scroll area for steps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(4)
        self.steps_layout.addStretch()

        scroll.setWidget(self.steps_container)
        layout.addWidget(scroll)

    @Slot(dict)
    def update_plan(self, plan_data: dict) -> None:
        """Update the plan display with new data.

        Args:
            plan_data: Dictionary with 'goal' and 'steps' keys.
        """
        self._current_plan = plan_data

        # Update goal
        goal = plan_data.get("goal", "No goal specified")
        self.goal_label.setText(f"Goal: {goal}")

        # Clear existing steps
        while self.steps_layout.count() > 1:  # Keep the stretch
            item = self.steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new steps
        steps = plan_data.get("steps", [])
        for i, step in enumerate(steps, 1):
            step_widget = PlanStepWidget(i, step)
            self.steps_layout.insertWidget(self.steps_layout.count() - 1, step_widget)

    @Slot(int, str)
    def update_step_status(self, step_index: int, status: str) -> None:
        """Update the status of a specific step.

        Args:
            step_index: Zero-based index of the step.
            status: New status (pending, running, completed, failed).
        """
        if self._current_plan and "steps" in self._current_plan:
            if 0 <= step_index < len(self._current_plan["steps"]):
                self._current_plan["steps"][step_index]["status"] = status
                self.update_plan(self._current_plan)

    def clear(self) -> None:
        """Clear the plan display."""
        self.goal_label.setText("No active plan")
        self._current_plan = None

        # Clear existing steps
        while self.steps_layout.count() > 1:
            item = self.steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_current_plan(self) -> dict | None:
        """Get the current plan data."""
        return self._current_plan
