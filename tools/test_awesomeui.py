"""Offline integration regressions for the awesomeUI migration."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
from awesomeui import Sidebar
from src.gui.widgets import NavigationSidebar
from src.gui.theme import ColorThemeManager

APP = QApplication.instance() or QApplication([])


class AwesomeUIIntegration(unittest.TestCase):
    def test_library_is_standalone_and_manifest_matches(self):
        manifest = json.loads((ROOT / 'awesomeui/upstream.json').read_text())
        for name, expected in manifest['sha256'].items():
            path = ROOT / 'awesomeui' / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, name)
            if path.suffix == '.py':
                for node in ast.walk(ast.parse(path.read_text())):
                    if isinstance(node, ast.ImportFrom):
                        self.assertFalse((node.module or '').startswith('src.'), name)
                    elif isinstance(node, ast.Import):
                        self.assertFalse(any(n.name.startswith('src.') for n in node.names), name)

    def test_main_window_navigation_gating_and_live_theme(self):
        from src.controllers.translator import Translator
        from src.devicemanagement.device_manager import DeviceManager
        from src.gui.main_window import MainWindow
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / 'settings.ini'), QSettings.IniFormat)
            previous = ColorThemeManager._inst
            with patch('src.gui.theme.theme_manager.QSettings', return_value=settings):
                ColorThemeManager._inst = ColorThemeManager()
            manager = DeviceManager()
            manager.pref_manager.settings = settings
            try:
                with patch.object(MainWindow, 'refresh_devices'), \
                     patch.object(MainWindow, '_load_last_preset'), \
                     patch.object(MainWindow, '_register_tweak_autosave'), \
                     patch('src.gui.main_window.DeviceMonitorThread.start'), \
                     patch('src.gui.ios.theme_manager.QSettings', return_value=settings), \
                     patch('PySide6.QtCore.QStandardPaths.writableLocation', return_value=directory):
                    window = MainWindow(manager, Translator(APP, settings))
                try:
                    self.assertIsInstance(window.ui.sidebar, Sidebar)
                    window.show()
                    APP.processEvents()
                    self.assertTrue(window.ui.sidebar.isHidden())
                    self.assertFalse(window.ios_settings.sidebar_switch.isChecked())
                    self.assertFalse(window.sidebar_enabled())
                    window.set_ios_page(4, animate=False)
                    switch = window.ios_settings.sidebar_switch
                    switch.setChecked(True)
                    APP.processEvents()
                    self.assertTrue(window.ui.sidebar.isVisible())
                    self.assertTrue(settings.value('ui/show_sidebar', False, type=bool))
                    self.assertEqual(window.ios_pages.currentIndex(), 4)
                    window.apply_theme(window.theme_manager.current_theme)
                    self.assertTrue(window.ui.sidebar.isVisible())
                    switch.setChecked(False)
                    APP.processEvents()
                    self.assertTrue(window.ui.sidebar.isHidden())
                    self.assertFalse(settings.value('ui/show_sidebar', True, type=bool))
                    self.assertEqual(window.ios_pages.currentIndex(), 4)
                    for index, name in ((0, 'homePageBtn'), (4, 'settingsPageBtn'),
                                        (12, 'presetsPageBtn'), (6, 'applyPageBtn')):
                        getattr(window.ui, name).click()
                        APP.processEvents()
                        self.assertEqual(window.ios_pages.currentIndex(), index)
                        self.assertEqual(window.ui.sidebar.current_item_id(), name)
                        self.assertIs(getattr(window.ui, name), window.ui.sidebar.item(name))
                    with patch('src.gui.main_window_mixins._hidden_feature_names',
                               return_value={'PosterBoard', 'Daemons'}):
                        window._apply_hidden_feature_gating()
                    self.assertTrue(window.ui.posterboardPageBtn.isHidden())
                    self.assertTrue(window.ui.daemonsPageBtn.isHidden())
                    # Hidden sidebars must catch up when they become visible.
                    ColorThemeManager.instance().set_accent('purple')
                    window.ui.sidebar.show()
                    APP.processEvents()
                    self.assertEqual(window.ui.sidebar.theme().active_indicator,
                                     ColorThemeManager.instance().accent_hex())
                    self.assertIn(ColorThemeManager.instance().colors.bg_secondary,
                                  window.ui.sidebar.styleSheet())
                    self.assertEqual(len(window.ui.sidebar._items), len(NavigationSidebar.ITEM_NAMES))
                    if os.environ.get('GOLDENNUGGET_UI_SCREENSHOT'):
                        window.grab().save(os.environ['GOLDENNUGGET_UI_SCREENSHOT'])
                finally:
                    window.close()
                    window.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            finally:
                ColorThemeManager._inst = previous


if __name__ == '__main__':
    unittest.main()
