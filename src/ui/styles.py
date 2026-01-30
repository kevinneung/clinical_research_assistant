"""QSS stylesheets for the Clinical Research Assistant UI."""


def get_stylesheet() -> str:
    """Get the main application stylesheet."""
    return """
    /* Main Window */
    QMainWindow {
        background-color: #f5f5f5;
    }

    /* Panels */
    QWidget#panel {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }

    /* Text Areas */
    QTextEdit {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 8px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }

    QTextEdit:focus {
        border: 1px solid #2196F3;
    }

    QTextEdit[readOnly="true"] {
        background-color: #fafafa;
    }

    /* Input Fields */
    QLineEdit {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 13px;
    }

    QLineEdit:focus {
        border: 1px solid #2196F3;
    }

    /* Buttons */
    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #1976D2;
    }

    QPushButton:pressed {
        background-color: #1565C0;
    }

    QPushButton:disabled {
        background-color: #BDBDBD;
    }

    QPushButton#approveButton {
        background-color: #4CAF50;
    }

    QPushButton#approveButton:hover {
        background-color: #43A047;
    }

    QPushButton#denyButton {
        background-color: #f44336;
    }

    QPushButton#denyButton:hover {
        background-color: #E53935;
    }

    QPushButton#secondaryButton {
        background-color: #757575;
    }

    QPushButton#secondaryButton:hover {
        background-color: #616161;
    }

    /* Tree View (Workspace) */
    QTreeView {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-size: 13px;
    }

    QTreeView::item {
        padding: 4px;
    }

    QTreeView::item:selected {
        background-color: #E3F2FD;
        color: #1976D2;
    }

    QTreeView::item:hover {
        background-color: #F5F5F5;
    }

    /* Headers */
    QLabel#header {
        font-size: 16px;
        font-weight: 600;
        color: #333333;
        padding: 8px 0;
    }

    QLabel#subheader {
        font-size: 14px;
        font-weight: 500;
        color: #666666;
        padding: 4px 0;
    }

    /* Splitter */
    QSplitter::handle {
        background-color: #e0e0e0;
    }

    QSplitter::handle:horizontal {
        width: 2px;
    }

    QSplitter::handle:vertical {
        height: 2px;
    }

    /* Scroll Bars */
    QScrollBar:vertical {
        background-color: #f5f5f5;
        width: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical {
        background-color: #BDBDBD;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #9E9E9E;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* Group Box */
    QGroupBox {
        font-weight: 500;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #666666;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #f5f5f5;
        border-top: 1px solid #e0e0e0;
        font-size: 12px;
        color: #666666;
    }

    /* Menu Bar */
    QMenuBar {
        background-color: white;
        border-bottom: 1px solid #e0e0e0;
    }

    QMenuBar::item {
        padding: 8px 12px;
    }

    QMenuBar::item:selected {
        background-color: #E3F2FD;
    }

    /* Dialog */
    QDialog {
        background-color: white;
    }
    """
