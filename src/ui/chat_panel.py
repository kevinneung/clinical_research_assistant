"""Chat panel widget for user interaction with agents."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QTextCursor


class ChatPanel(QWidget):
    """Chat interface for communicating with the agent system."""

    message_sent = Signal(str)  # Emitted when user sends a message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the chat panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QLabel("Chat")
        header.setObjectName("header")
        layout.addWidget(header)

        # Message display area
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setPlaceholderText(
            "Chat with the Clinical Research Assistant.\n"
            "Describe your research task or ask questions about clinical trials."
        )
        layout.addWidget(self.message_display)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Describe your research task...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setFixedWidth(80)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

    @Slot()
    def send_message(self) -> None:
        """Send the current input message."""
        text = self.input_field.text().strip()
        if text:
            self.append_message("You", text)
            self.message_sent.emit(text)
            self.input_field.clear()

    @Slot(str, str)
    def append_message(self, sender: str, content: str) -> None:
        """Append a message to the display.

        Args:
            sender: Name of the message sender.
            content: Message content.
        """
        # Format the message with sender
        if sender == "You":
            formatted = f'<p style="color: #1976D2;"><b>{sender}:</b> {content}</p>'
        elif sender == "Assistant":
            formatted = f'<p style="color: #333333;"><b>{sender}:</b> {content}</p>'
        else:
            formatted = f'<p style="color: #666666;"><b>{sender}:</b> {content}</p>'

        self.message_display.append(formatted)

        # Scroll to bottom
        cursor = self.message_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.message_display.setTextCursor(cursor)

    @Slot(str)
    def append_streaming(self, token: str) -> None:
        """Append a streaming token without newline.

        Args:
            token: Token to append.
        """
        cursor = self.message_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(token)
        self.message_display.setTextCursor(cursor)

    @Slot()
    def start_assistant_message(self) -> None:
        """Start a new assistant message for streaming."""
        self.message_display.append('<p style="color: #333333;"><b>Assistant:</b> ')

    @Slot()
    def end_assistant_message(self) -> None:
        """End the current assistant message."""
        cursor = self.message_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText("</p>")
        self.message_display.setTextCursor(cursor)

    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable the input controls.

        Args:
            enabled: Whether input should be enabled.
        """
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def clear(self) -> None:
        """Clear all messages from the display."""
        self.message_display.clear()
