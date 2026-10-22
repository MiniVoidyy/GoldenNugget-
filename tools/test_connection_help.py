"""Connection assistance stays inline and never pretends to detect Trust."""
import os
import sys
from pathlib import Path
from unittest.mock import Mock
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QDialogButtonBox
from src.gui.ios.connect_placeholder import ConnectDevicePlaceholder
from src.gui.dialogs.reset_dialog import ResetDialog


class ConnectionHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_scan_status_and_help_are_inline(self):
        window = Mock()
        page = ConnectDevicePlaceholder(window)
        page._refresh_btn.click()
        window.refresh_devices.assert_called_once()
        page.set_scan_status('Checking devices', busy=True)
        self.assertFalse(page._refresh_btn.isEnabled())
        page.set_scan_status('Device locked', busy=False)
        self.assertTrue(page._refresh_btn.isEnabled())
        self.assertEqual(page._scan_status.text(), 'Device locked')
        page._diagnostics_btn.click()
        self.assertFalse(page._help_detail.isHidden())
        page._continue_btn.click()
        window.continue_without_device.assert_called_once()
        self.assertIsNone(self.app.activeModalWidget())
        page.close()
        page.deleteLater()
        self.app.processEvents()

    def test_restore_defaults_requires_a_section(self):
        manager = Mock()
        manager.get_current_device_version.return_value = '27.0'
        manager.get_current_device_model.return_value = 'iPhone17,3'
        dialog = ResetDialog(manager)
        button = dialog.buttonBox.button(QDialogButtonBox.Ok)
        self.assertFalse(button.isEnabled())
        from src.gui.pages.pages_list import Page
        dialog.toggle_page(True, Page.Springboard)
        self.assertTrue(button.isEnabled())
        dialog.toggle_page(False, Page.Springboard)
        self.assertFalse(button.isEnabled())
        dialog.close()
        dialog.deleteLater()
        self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
