"""Approval dialog for human-in-the-loop decisions."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QScrollArea,
    QWidget,
    QFrame,
)
from PySide6.QtCore import Qt

# Agent display names and colors
AGENT_DISPLAY_NAMES = {
    "project_manager": "Project Manager",
    "document_maker": "Document Maker",
    "email_drafter": "Email Drafter",
}

AGENT_COLORS = {
    "project_manager": "#2196F3",
    "document_maker": "#009688",
    "email_drafter": "#7B1FA2",
}


class ApprovalDialog(QDialog):
    """Modal dialog for human approval of agent actions."""

    def __init__(self, action: str, details: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Action Requires Approval")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        self._setup_ui(action, details)

    def _setup_ui(self, action: str, details: dict) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Warning icon and header
        header_layout = QHBoxLayout()
        warning_label = QLabel("⚠️")
        warning_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(warning_label)

        title_label = QLabel("Approval Required")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Action description
        action_group = QGroupBox("Proposed Action")
        action_layout = QVBoxLayout(action_group)

        action_label = QLabel(action)
        action_label.setWordWrap(True)
        action_label.setStyleSheet("font-size: 14px; padding: 8px;")
        action_layout.addWidget(action_label)

        layout.addWidget(action_group)

        # Details section — rich plan view or fallback
        steps = details.get("steps", [])
        if isinstance(steps, list) and steps:
            self._build_plan_details(layout, details)
        else:
            self._build_flat_details(layout, details)

        # Notes input
        notes_group = QGroupBox("Notes (optional)")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Add any notes or feedback about this action..."
        )
        self.notes_input.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_input)

        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.deny_btn = QPushButton("Deny")
        self.deny_btn.setObjectName("denyButton")
        self.deny_btn.setMinimumWidth(100)
        self.deny_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.deny_btn)

        self.approve_btn = QPushButton("Approve")
        self.approve_btn.setObjectName("approveButton")
        self.approve_btn.setMinimumWidth(100)
        self.approve_btn.clicked.connect(self.accept)
        self.approve_btn.setDefault(True)
        button_layout.addWidget(self.approve_btn)

        layout.addLayout(button_layout)

    def _build_plan_details(self, layout: QVBoxLayout, details: dict) -> None:
        """Build a rich plan view with goal and scrollable step list."""
        details_group = QGroupBox("Plan Details")
        details_layout = QVBoxLayout(details_group)

        # Goal
        goal = details.get("goal", "")
        if goal:
            goal_label = QLabel(f"<b>Goal:</b> {goal}")
            goal_label.setWordWrap(True)
            goal_label.setStyleSheet("font-size: 13px; padding: 4px 0;")
            details_layout.addWidget(goal_label)

        # Scrollable step list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        steps_container = QWidget()
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(8)

        steps = details.get("steps", [])
        for i, step in enumerate(steps, 1):
            step_widget = self._build_step_widget(i, step)
            steps_layout.addWidget(step_widget)

        steps_layout.addStretch()
        scroll_area.setWidget(steps_container)
        details_layout.addWidget(scroll_area)

        # Agents summary
        agents = details.get("estimated_agents", [])
        if agents:
            agent_names = [
                AGENT_DISPLAY_NAMES.get(a, a.replace("_", " ").title())
                for a in agents
            ]
            agents_label = QLabel(
                f"<b>Agents involved:</b> {', '.join(agent_names)}"
            )
            agents_label.setStyleSheet("font-size: 12px; padding-top: 4px;")
            details_layout.addWidget(agents_label)

        layout.addWidget(details_group, stretch=1)

    def _build_step_widget(self, number: int, step: dict) -> QFrame:
        """Build a single step display widget."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background-color: #fafafa; border: 1px solid #e0e0e0; "
            "border-radius: 6px; padding: 8px; }"
        )

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.setSpacing(4)

        # Top row: step number, agent badge, approval warning
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        step_num_label = QLabel(f"<b>Step {number}</b>")
        step_num_label.setStyleSheet("font-size: 12px;")
        top_row.addWidget(step_num_label)

        agent_key = step.get("agent", "unknown")
        agent_name = AGENT_DISPLAY_NAMES.get(
            agent_key, agent_key.replace("_", " ").title()
        )
        agent_color = AGENT_COLORS.get(agent_key, "#757575")
        agent_badge = QLabel(agent_name)
        agent_badge.setStyleSheet(
            f"background-color: {agent_color}; color: white; "
            f"border-radius: 4px; padding: 2px 8px; font-size: 11px; "
            f"font-weight: bold;"
        )
        top_row.addWidget(agent_badge)

        top_row.addStretch()

        if step.get("requires_approval"):
            approval_label = QLabel("⚠ Requires Approval")
            approval_label.setStyleSheet(
                "color: #F57C00; font-size: 11px; font-weight: bold;"
            )
            top_row.addWidget(approval_label)

        frame_layout.addLayout(top_row)

        # Description
        desc = step.get("description", "")
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #424242; padding-top: 2px;")
        frame_layout.addWidget(desc_label)

        return frame

    def _build_flat_details(self, layout: QVBoxLayout, details: dict) -> None:
        """Build the original flat key-value details view (fallback)."""
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)

        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setPlainText(self._format_details(details))
        details_text.setMaximumHeight(150)
        details_text.setStyleSheet("background-color: #fafafa;")
        details_layout.addWidget(details_text)

        layout.addWidget(details_group)

    def _format_details(self, details: dict) -> str:
        """Format details dictionary for display.

        Args:
            details: Dictionary of action details.

        Returns:
            Formatted string representation.
        """
        if not details:
            return "No additional details provided."

        lines = []
        for key, value in details.items():
            # Format the key nicely
            formatted_key = key.replace("_", " ").title()

            # Format the value
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                value = "\n  ".join(f"{k}: {v}" for k, v in value.items())

            lines.append(f"{formatted_key}: {value}")

        return "\n".join(lines)

    def get_notes(self) -> str:
        """Get the researcher's notes.

        Returns:
            The notes entered by the researcher.
        """
        return self.notes_input.toPlainText()

    def get_result(self) -> tuple[bool, str]:
        """Get the approval result and notes.

        Returns:
            Tuple of (approved, notes).
        """
        return (self.result() == QDialog.Accepted, self.get_notes())
