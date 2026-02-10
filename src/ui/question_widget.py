"""Multiple-choice question widget for agent interactions."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Signal, Slot


class QuestionWidget(QFrame):
    """Displays a multiple-choice question from the agent.

    Hidden by default. Call ``show_question`` to populate options and reveal.
    An "Other" free-text row is always shown at the bottom.
    """

    answer_selected = Signal(str)  # Emitted with the chosen answer text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("questionWidget")
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        # Question label
        self._question_label = QLabel()
        self._question_label.setObjectName("questionLabel")
        self._question_label.setWordWrap(True)
        self._layout.addWidget(self._question_label)

        # Container for dynamic option buttons (replaced each question)
        self._options_layout = QVBoxLayout()
        self._options_layout.setSpacing(6)
        self._layout.addLayout(self._options_layout)

        # "Other" free-text row
        other_layout = QHBoxLayout()
        other_layout.setSpacing(8)

        self._other_input = QLineEdit()
        self._other_input.setPlaceholderText("Other (type your answer)...")
        self._other_input.returnPressed.connect(self._submit_other)
        other_layout.addWidget(self._other_input)

        self._other_button = QPushButton("Submit")
        self._other_button.setObjectName("optionButton")
        self._other_button.setFixedWidth(80)
        self._other_button.clicked.connect(self._submit_other)
        other_layout.addWidget(self._other_button)

        self._layout.addLayout(other_layout)

    # -- public API ----------------------------------------------------------

    @Slot(str, list)
    def show_question(self, question: str, options: list[str]) -> None:
        """Populate the widget with a new question and show it.

        Args:
            question: The question text.
            options: List of answer choices (buttons).
        """
        self._question_label.setText(question)
        self._other_input.clear()

        # Clear previous option buttons
        while self._options_layout.count():
            item = self._options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create fresh option buttons
        for text in options:
            btn = QPushButton(text)
            btn.setObjectName("optionButton")
            btn.clicked.connect(lambda checked=False, t=text: self._pick(t))
            self._options_layout.addWidget(btn)

        self.show()

    # -- private slots -------------------------------------------------------

    def _pick(self, text: str) -> None:
        self.hide()
        self.answer_selected.emit(text)

    @Slot()
    def _submit_other(self) -> None:
        text = self._other_input.text().strip()
        if text:
            self.hide()
            self.answer_selected.emit(text)
