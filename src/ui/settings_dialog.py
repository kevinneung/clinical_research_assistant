"""Settings dialog for configuring per-agent custom instructions."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QWidget,
    QLabel,
)
from PySide6.QtCore import Qt

from src.services.prompt_store import PromptStore

# Agent display metadata
_AGENTS = [
    ("orchestrator", "Orchestrator", "Plans tasks and delegates to other agents"),
    ("project_manager", "Project Manager", "Cost estimation, timelines, CSV export"),
    ("document_maker", "Document Maker", "Compliance documents (ICF, Protocol, IB, IRB)"),
    ("email_drafter", "Email Drafter", "Professional correspondence"),
]


class SettingsDialog(QDialog):
    """Modal dialog for editing per-agent custom instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self.setMinimumHeight(520)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        self._store = PromptStore()
        self._editors: dict[str, QPlainTextEdit] = {}
        self._setup_ui()
        self._load()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Agent Instructions")
        heading.setObjectName("header")
        layout.addWidget(heading)

        description = QLabel(
            "Add custom instructions that are appended to each agent's built-in "
            "system prompt. Changes take effect on the next agent run."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666666; font-size: 12px; padding-bottom: 4px;")
        layout.addWidget(description)

        # Scrollable area for agent sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        for key, display_name, desc in _AGENTS:
            group = QGroupBox(display_name)
            group_layout = QVBoxLayout(group)

            hint = QLabel(desc)
            hint.setStyleSheet("color: #888888; font-size: 11px;")
            group_layout.addWidget(hint)

            editor = QPlainTextEdit()
            editor.setPlaceholderText(
                f"Additional instructions for {display_name}...\n"
                f"(e.g., 'Always respond in bullet points')"
            )
            editor.setMaximumHeight(90)
            group_layout.addWidget(editor)

            clear_row = QHBoxLayout()
            clear_row.addStretch()
            clear_btn = QPushButton("Clear")
            clear_btn.setObjectName("secondaryButton")
            clear_btn.setFixedWidth(70)
            clear_btn.clicked.connect(lambda checked=False, e=editor: e.clear())
            clear_row.addWidget(clear_btn)
            group_layout.addLayout(clear_row)

            container_layout.addWidget(group)
            self._editors[key] = editor

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("approveButton")
        save_btn.setMinimumWidth(90)
        save_btn.clicked.connect(self._save_and_accept)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load(self) -> None:
        """Load persisted instructions into editors."""
        data = self._store.get_all()
        for key, editor in self._editors.items():
            editor.setPlainText(data.get(key, ""))

    def _save_and_accept(self) -> None:
        """Persist editor contents and close."""
        for key, editor in self._editors.items():
            self._store.set(key, editor.toPlainText())
        self.accept()
