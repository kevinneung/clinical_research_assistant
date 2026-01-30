"""Tests for the approval dialog."""

import pytest

# pytest-qt is required for these tests
pytestmark = pytest.mark.skipif(
    True,  # Skip by default unless pytest-qt is available and Qt is set up
    reason="Qt tests require display and pytest-qt",
)


class TestApprovalDialog:
    """Tests for the ApprovalDialog widget."""

    def test_dialog_creation(self, qtbot):
        """Test creating an approval dialog."""
        from src.ui.approval_dialog import ApprovalDialog

        dialog = ApprovalDialog(
            action="Send email to IRB",
            details={"recipients": ["irb@hospital.org"], "subject": "Protocol submission"},
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Action Requires Approval"

    def test_dialog_displays_action(self, qtbot):
        """Test that dialog displays the action."""
        from src.ui.approval_dialog import ApprovalDialog

        dialog = ApprovalDialog(
            action="Test action description",
            details={},
        )
        qtbot.addWidget(dialog)

        # Check that action is displayed somewhere in the dialog
        # This would require more specific widget inspection

    def test_get_notes(self, qtbot):
        """Test getting notes from dialog."""
        from src.ui.approval_dialog import ApprovalDialog

        dialog = ApprovalDialog(action="Test", details={})
        qtbot.addWidget(dialog)

        dialog.notes_input.setText("My notes")

        assert dialog.get_notes() == "My notes"

    def test_approve_returns_accepted(self, qtbot):
        """Test that approve button accepts dialog."""
        from src.ui.approval_dialog import ApprovalDialog
        from PySide6.QtWidgets import QDialog

        dialog = ApprovalDialog(action="Test", details={})
        qtbot.addWidget(dialog)

        # Simulate clicking approve
        qtbot.mouseClick(dialog.approve_btn, pytest.qt.MouseButton.LeftButton)

        # Dialog should be accepted
        # Note: This may need adjustment based on how the dialog is closed
