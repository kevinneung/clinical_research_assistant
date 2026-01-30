"""Approval dialog for human-in-the-loop decisions."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QGroupBox,
)
from PySide6.QtCore import Qt


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

        # Details group
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)

        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setPlainText(self._format_details(details))
        details_text.setMaximumHeight(150)
        details_text.setStyleSheet("background-color: #fafafa;")
        details_layout.addWidget(details_text)

        layout.addWidget(details_group)

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
