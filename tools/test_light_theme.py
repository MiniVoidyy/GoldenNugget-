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

from PySide6.QtCore import QSettings, QCoreApplication, QEvent
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
        # These tests cover the light theme itself, so it is made available here.
        self.patch_light = patch('src.gui.theme.theme_manager.LIGHT_MODE_AVAILABLE', True)
        self.patch_light.start()
        self.addCleanup(self.patch_light.stop)
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

    def test_dark_on_every_start_while_light_is_unavailable(self):
        self.manager.set_mode('light')
        with patch('src.gui.theme.theme_manager.LIGHT_MODE_AVAILABLE', False):
            restored = ColorThemeManager()
        self.assertEqual(restored.mode, 'dark')
        self.assertEqual(restored.colors.bg_primary, DARK.bg_primary)
        self.assertEqual(self.settings.value('color_mode'), 'light', 'the saved choice is kept')

    def test_os_colour_scheme_never_overrides_the_saved_mode(self):
        from PySide6.QtCore import QObject, Qt, Signal

        class Hints(QObject):
            colorSchemeChanged = Signal(object)

            def __init__(self):
                super().__init__()
                self.scheme = None

            def setColorScheme(self, scheme):
                self.scheme = scheme

        class App:
            def __init__(self):
                self.hints = Hints()
                self.palette = None

            def styleHints(self):
                return self.hints

            def setPalette(self, palette):
                self.palette = palette

        app = App()
        self.manager.apply_to_app(app)
        self.assertEqual(app.hints.scheme, Qt.ColorScheme.Dark, 'dark is pinned by default')
        # The OS (or anything else) switches to light: the saved mode wins.
        app.hints.scheme = Qt.ColorScheme.Light
        app.hints.colorSchemeChanged.emit(Qt.ColorScheme.Light)
        self.assertEqual(app.hints.scheme, Qt.ColorScheme.Dark)
        self.assertEqual(app.palette.window().color().name().lower(), DARK.bg_primary.lower())
        # A replaced manager stays out of it.
        ColorThemeManager._inst = object()
        app.hints.scheme = Qt.ColorScheme.Light
        app.hints.colorSchemeChanged.emit(Qt.ColorScheme.Light)
        self.assertEqual(app.hints.scheme, Qt.ColorScheme.Light)
        ColorThemeManager._inst = self.manager
        # An explicit light choice is pinned as light.
        with patch('src.gui.theme.theme_manager.QGuiApplication.instance', return_value=app):
            self.manager.set_mode('light')
        self.assertEqual(app.hints.scheme, Qt.ColorScheme.Light)

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

    def test_every_page_drops_the_old_palette_after_a_live_toggle(self):
        """Pages re-theme lazily (set_ios_page checks a revision), so a page that
        was NOT on screen when the mode flipped must still come up in the new
        palette. Guards the lazy path: dark-only colours must not survive on any
        page reached after switching to light, and vice versa."""
        from src.controllers.translator import Translator
        from src.devicemanagement.device_manager import DeviceManager
        from src.gui.main_window import MainWindow
        from PySide6.QtWidgets import QWidget
        dm = DeviceManager()
        dm.pref_manager.settings = self.settings
        with patch.object(MainWindow, 'refresh_devices'), patch.object(MainWindow, '_load_last_preset'), \
             patch.object(MainWindow, '_register_tweak_autosave'), \
             patch('src.gui.main_window.DeviceMonitorThread.start'), \
             patch('src.gui.ios.theme_manager.QSettings', return_value=self.settings), \
             patch('PySide6.QtCore.QStandardPaths.writableLocation', return_value=self.tmp.name):
            window = MainWindow(dm, Translator(APP, self.settings))
        slots = ('bg_primary', 'bg_secondary', 'bg_tertiary', 'bg_input', 'text_primary', 'text_secondary')

        def only_in(a, b):
            return {getattr(a, slot).lower() for slot in slots} - {getattr(b, slot).lower() for slot in slots}

        try:
            window.show()
            window.content_stack.setCurrentIndex(1)
            window.set_ios_page(0, animate=False)
            for mode, old in (('light', DARK), ('dark', LIGHT)):
                self.manager.set_mode(mode)
                window._on_color_theme_changed()
                stale = only_in(old, self.manager.colors)
                for index in range(window.ios_pages.count()):
                    window.set_ios_page(index, animate=False)
                    APP.processEvents()
                    page = window.ios_pages.widget(index)
                    # Hidden widgets are re-themed when they are next shown
                    # (connect_visible_theme), so only what is on screen counts.
                    shown = [w for w in [page, *page.findChildren(QWidget)] if w.isVisibleTo(page)]
                    leftovers = sorted(
                        f'{type(w).__name__}#{w.objectName()}:{color}' for w in shown
                        for color in stale if color in w.styleSheet().lower())
                    self.assertEqual(
                        leftovers, [], f'{type(page).__name__} (index {index}) still carries {old is DARK and "dark" or "light"} colours after switching to {mode}')
                # The result card is hidden until an operation finishes; it must come
                # up in the current palette the moment it appears.
                window.set_ios_page(0, animate=False)
                home = window.ios_home
                for name in ('result_card',):
                    card = getattr(home, name)
                    was_hidden = card.isHidden()
                    card.show()
                    APP.processEvents()
                    sheets = ' '.join(w.styleSheet().lower() for w in [card, *card.findChildren(QWidget)])
                    self.assertEqual(sorted(color for color in stale if color in sheets), [],
                                     f'home.{name} appeared with stale colours after switching to {mode}')
                    card.setVisible(not was_hidden)
        finally:
            window.close()
            window.deleteLater()
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


if __name__ == '__main__':
    unittest.main()
