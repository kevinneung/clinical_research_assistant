"""Workspace file browser panel."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Signal, Slot, Qt, QModelIndex
from PySide6.QtGui import QFileSystemModel, QDesktopServices, QAction
from PySide6.QtCore import QUrl


class WorkspacePanel(QWidget):
    """File browser for the project workspace."""

    file_selected = Signal(str)  # Emitted when a file is selected
    file_opened = Signal(str)  # Emitted when a file is double-clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workspace_path: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the workspace panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header with refresh button
        header_layout = QHBoxLayout()

        header = QLabel("Workspace")
        header.setObjectName("header")
        header_layout.addWidget(header)

        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(70)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # File system model and tree view
        self.model = QFileSystemModel()
        self.model.setRootPath("")

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)

        # Hide unnecessary columns (Size, Type, Date Modified)
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)

        # Connect signals
        self.tree_view.clicked.connect(self._on_item_clicked)
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.tree_view)

        # Status label
        self.status_label = QLabel("No workspace selected")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.status_label)

    def set_workspace(self, path: str) -> None:
        """Set the workspace directory to display.

        Args:
            path: Path to the workspace directory.
        """
        self._workspace_path = path
        path_obj = Path(path)

        if path_obj.exists() and path_obj.is_dir():
            index = self.model.setRootPath(path)
            self.tree_view.setRootIndex(index)
            self.status_label.setText(f"Workspace: {path_obj.name}")
        else:
            self.status_label.setText("Invalid workspace path")

    def get_workspace(self) -> str | None:
        """Get the current workspace path."""
        return self._workspace_path

    @Slot()
    def refresh(self) -> None:
        """Refresh the file tree."""
        if self._workspace_path:
            # Force refresh by re-setting the root path
            self.model.setRootPath("")
            index = self.model.setRootPath(self._workspace_path)
            self.tree_view.setRootIndex(index)

    @Slot(QModelIndex)
    def _on_item_clicked(self, index: QModelIndex) -> None:
        """Handle item click."""
        path = self.model.filePath(index)
        if path:
            self.file_selected.emit(path)

    @Slot(QModelIndex)
    def _on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handle item double-click (open file)."""
        path = self.model.filePath(index)
        if path and Path(path).is_file():
            self.file_opened.emit(path)
            # Open with default application
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot()
    def _show_context_menu(self, position) -> None:
        """Show context menu for file operations."""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        path = self.model.filePath(index)
        is_dir = Path(path).is_dir()

        menu = QMenu(self)

        # Open action
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._open_path(path))
        menu.addAction(open_action)

        # Show in explorer
        show_action = QAction("Show in Explorer", self)
        show_action.triggered.connect(lambda: self._show_in_explorer(path))
        menu.addAction(show_action)

        menu.addSeparator()

        if is_dir:
            # New file action
            new_file_action = QAction("New File...", self)
            new_file_action.triggered.connect(lambda: self._create_new_file(path))
            menu.addAction(new_file_action)

            # New folder action
            new_folder_action = QAction("New Folder...", self)
            new_folder_action.triggered.connect(lambda: self._create_new_folder(path))
            menu.addAction(new_folder_action)

        menu.addSeparator()

        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_path(path))
        menu.addAction(delete_action)

        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _open_path(self, path: str) -> None:
        """Open a file or folder."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _show_in_explorer(self, path: str) -> None:
        """Show the path in file explorer."""
        path_obj = Path(path)
        if path_obj.is_file():
            path = str(path_obj.parent)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _create_new_file(self, parent_path: str) -> None:
        """Create a new file in the given directory."""
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            new_path = Path(parent_path) / name
            try:
                new_path.touch()
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file: {e}")

    def _create_new_folder(self, parent_path: str) -> None:
        """Create a new folder in the given directory."""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            new_path = Path(parent_path) / name
            try:
                new_path.mkdir(parents=True, exist_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {e}")

    def _delete_path(self, path: str) -> None:
        """Delete a file or folder after confirmation."""
        path_obj = Path(path)
        name = path_obj.name

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if path_obj.is_file():
                    path_obj.unlink()
                else:
                    import shutil
                    shutil.rmtree(path_obj)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {e}")
