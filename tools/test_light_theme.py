"""Offline color-mode persistence, contrast and live-widget regressions."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'qt'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings, QCoreApplication, QEvent, QTranslator
from PySide6.QtGui import QPalette, QColor
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QLabel
from src.gui.theme import ColorThemeManager, LIGHT, DARK, LIGHT_ACCENT_PRESETS, STYLES, t

APP = QApplication.instance() or QApplication([])
APP.setStyle('Fusion')


def contrast(first, second):
    def luminance(hex_color):
        values = [int(hex_color[pos:pos + 2], 16) / 255 for pos in (1, 3, 5)]
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, (.2126, .7152, .0722)))
    dark, light = sorted((luminance(first), luminance(second)))
    return (light + .05) / (dark + .05)


class Themes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name) / 'appearance.ini'), QSettings.IniFormat)
        self.old_manager = ColorThemeManager._inst
        self.old_palette = APP.palette()
        self.patch_settings = patch('src.gui.theme.theme_manager.QSettings', return_value=self.settings)
        self.patch_settings.start()
        self.addCleanup(self.patch_settings.stop)
        self.manager = ColorThemeManager()
        ColorThemeManager._inst = self.manager
        self.addCleanup(self.restore)

    def restore(self):
        ColorThemeManager._inst = self.old_manager
        APP.setPalette(self.old_palette)

    def test_default_and_persistence_keep_accent_independent(self):
        self.assertEqual(self.manager.mode, 'dark')
        self.assertTrue(self.manager.is_dark)
        self.manager.set_accent('yellow')
        self.manager.set_mode('light')
        restored = ColorThemeManager()
        self.assertEqual(restored.mode, 'light')
        self.assertEqual(restored.accent_name, 'yellow')
        self.assertEqual(restored.colors.accent, LIGHT_ACCENT_PRESETS['yellow'][0])
        restored.set_mode('dark')
        self.assertEqual(restored.accent_name, 'yellow')
        self.assertEqual(restored.colors.bg_primary, DARK.bg_primary)

    def test_invalid_preferences_fall_back_and_noop_does_not_emit(self):
        self.settings.setValue('color_mode', 'unsupported')
        self.settings.setValue('accent_color', 'unknown')
        restored = ColorThemeManager()
        self.assertEqual((restored.mode, restored.accent_name), ('dark', 'blue'))
        spy = QSignalSpy(self.manager.theme_changed)
        self.manager.set_mode('dark')
        self.manager.set_mode('invalid')
        self.manager.set_accent('unknown')
        self.assertEqual(spy.count(), 0)
        self.manager.set_mode('light')
        self.assertEqual(spy.count(), 1)

    def test_light_text_semantics_and_all_accents_have_readable_contrast(self):
        self.manager.set_mode('light')
        surfaces = (LIGHT.bg_primary, LIGHT.bg_secondary, LIGHT.bg_tertiary, LIGHT.bg_input,
                    LIGHT.bg_elevated, LIGHT.surface_hover)
        for color in (LIGHT.text_primary, LIGHT.text_secondary, LIGHT.error, LIGHT.success, LIGHT.warning):
            for surface in surfaces:
                self.assertGreaterEqual(contrast(color, surface), 4.5, (color, surface))
        for name in LIGHT_ACCENT_PRESETS:
            self.manager.set_accent(name)
            c = self.manager.colors
            for color in (c.accent, c.accent_hover, c.accent_pressed):
                self.assertGreaterEqual(contrast(color, c.text_inverse), 4.5, name)
            for surface in surfaces:
                self.assertGreaterEqual(contrast(c.accent, surface), 4.5, name)
            self.assertEqual(self.manager.accent_hex(), c.accent)
            self.assertEqual(self.manager.accent_rgb(), QColor(c.accent).getRgb()[:3])
            self.assertEqual(c.selection, c.accent)

    def test_native_roles_update_for_active_and_inactive_windows(self):
        for mode in ('light', 'dark', 'light'):
            self.manager.set_mode(mode)
            c = self.manager.colors
            for group in (QPalette.Active, QPalette.Inactive):
                palette = self.manager.build_palette()
                self.assertEqual(palette.color(group, QPalette.Base).name(), c.bg_input.lower())
                self.assertEqual(palette.color(group, QPalette.Text).name(), c.text_primary.lower())
                self.assertEqual(palette.color(group, QPalette.HighlightedText).name(), c.text_inverse.lower())
                self.assertEqual(palette.color(group, QPalette.ToolTipText).name(), c.text_primary.lower())
            self.assertEqual(APP.palette().color(QPalette.Window).name(), c.bg_primary.lower())
            self.assertEqual(palette.color(QPalette.Disabled, QPalette.Text).name(), c.text_disabled.lower())

    def test_every_shared_template_renders_in_both_modes(self):
        for mode in ('dark', 'light'):
            self.manager.set_mode(mode)
            for key, template in STYLES.items():
                if key == 'accent_swatch':
                    from src.gui.theme import themed_stylesheet
                    rendered = themed_stylesheet(key, swatch=self.manager.accent_hex())
                else:
                    rendered = t(key)
                self.assertTrue(rendered.strip(), key)

    def test_swatch_numeric_dialog_and_about_follow_live_changes(self):
        from src.gui.theme import AccentPicker
        from src.gui.ios.components import NumberInputDialog
        from src.gui.dialogs.dialogs import AboutProgramDialog
        picker = AccentPicker()
        numeric = NumberInputDialog('Number', 1.5, 0, 10, step=.5)
        about = AboutProgramDialog()
        try:
            self.manager.set_mode('light')
            self.manager.set_accent('green')
            APP.processEvents()
            self.assertTrue(picker._buttons['green'].isChecked())
            self.assertIn(self.manager.colors.text_primary, picker._buttons['green'].styleSheet())
            self.assertIn(self.manager.colors.text_primary, numeric.spin.styleSheet())
            self.assertIn(self.manager.colors.text_inverse, about.styleSheet())
            self.assertNotIn(DARK.text_secondary, ''.join(label.styleSheet() for label in about.findChildren(QLabel)))
        finally:
            for widget in (picker, numeric, about):
                widget.close()
                widget.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_settings_has_no_mode_switch_and_rethemes_without_editing_tweaks(self):
        from src.controllers.translator import Translator
        from src.devicemanagement.device_manager import DeviceManager
        from src.gui.main_window import MainWindow
        from src.tweaks.tweaks import tweaks
        dm = DeviceManager()
        dm.pref_manager.settings = self.settings
        with patch.object(MainWindow, 'refresh_devices'), patch.object(MainWindow, '_load_last_preset'), \
             patch.object(MainWindow, '_register_tweak_autosave'), \
             patch('src.gui.main_window.DeviceMonitorThread.start'), \
             patch('src.gui.ios.theme_manager.QSettings', return_value=self.settings), \
             patch('PySide6.QtCore.QStandardPaths.writableLocation', return_value=self.tmp.name):
            window = MainWindow(dm, Translator(APP, self.settings))
        try:
            page = window.ios_settings
            window.show()
            window.content_stack.setCurrentIndex(1)
            window.set_ios_page(4, animate=False)
            APP.processEvents()
            self.assertFalse(hasattr(page, 'color_theme_combo'))
            before = {tid: (tweak.enabled, repr(tweak.value)) for tid, tweak in tweaks.items()}
            for mode in ('light', 'dark', 'light'):
                self.manager.set_mode(mode)
                window._on_color_theme_changed()
                APP.processEvents()
                self.assertEqual(self.manager.mode, mode)
                labels = [label for label in page.findChildren(QLabel) if label.property('theme_style_key')]
                self.assertTrue(labels)
                for label in labels:
                    self.assertEqual(label.styleSheet(), t(label.property('theme_style_key')))
                    self.assertIn('transparent', label.styleSheet())
            self.assertEqual(before, {tid: (tweak.enabled, repr(tweak.value)) for tid, tweak in tweaks.items()})
            self.assertEqual(ColorThemeManager().mode, 'light')
        finally:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_russian_theme_labels_are_shipped(self):
        translator = QTranslator()
        path = Path(__file__).resolve().parents[1] / 'src/qt/translations/Nugget_ru.qm'
        self.assertTrue(translator.load(str(path)))
        self.assertEqual(translator.translate('Nugget', 'Light'), 'Светлая')
        self.assertEqual(translator.translate('Nugget', 'Dark'), 'Тёмная')


if __name__ == '__main__':
    unittest.main()
