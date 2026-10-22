"""GoldenNugget's theme adapter for the shared awesomeUI controls.

Keep application settings and theme ownership here; implementations live in awesomeui.
"""
from awesomeui import configure_theme, Sidebar, SidebarTheme
from src.gui.theme import ColorThemeManager, t, theme_pixmap
from src.gui.theme.theme_manager import connect_visible_theme

configure_theme(manager=ColorThemeManager.instance, stylesheet=t,
                pixmap=theme_pixmap, connect=connect_visible_theme)

from awesomeui.controls import (
    IOSSearchField,
    IOSSegmentedFilter,
    IOSSearchEmpty,
    IOSSectionHeader,
    IOSCard,
    IOSCollapsibleSection,
    IOSNavBar,
    IOSValueRow,
    IOSSettingsRow,
    IOSSettingsAction,
    IOSPrimaryButton,
    IOSDangerButton,
    IOSSwitch,
    _auto_retheme,
)


class NavigationSidebar(Sidebar):
    """awesomeUI navigation with the existing page-controller bindings."""

    ITEM_NAMES = (
        "homePageBtn", "posterboardPageBtn", "gestaltPageBtn", "euEnablerPageBtn",
        "statusBarPageBtn", "passcodePageBtn", "springboardOptionsPageBtn",
        "internalOptionsPageBtn", "liquidGlassPageBtn", "daemonsPageBtn",
        "iconThemesPageBtn", "presetsPageBtn", "applyPageBtn", "settingsPageBtn",
    )

    def __init__(self, ui, parent=None):
        super().__init__(parent, collapsible=False)
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtGui import QIcon
        for name in self.ITEM_NAMES:
            if name == "posterboardPageBtn":
                ui.sidebarDiv1 = self.add_separator()
            if name == "applyPageBtn":
                ui.sidebarDiv2 = self.add_separator()
            old = getattr(ui, name, None)
            text = old.text() if old else QCoreApplication.translate("Nugget", "Presets")
            icon = old.icon() if old else QIcon(":/icon/folder.svg")
            item = self.add_item(name, text, icon)
            if old is not None:
                item.setEnabled(old.isEnabled())
                item.setVisible(not old.isHidden())
                item.setToolTip(old.toolTip())
                item.setChecked(old.isChecked())
            setattr(ui, name, item)
        self._retheme()
        _auto_retheme(self)

    def _retheme(self):
        colors = ColorThemeManager.instance().colors
        self.set_theme(SidebarTheme(
            background=colors.bg_secondary, border=colors.border,
            text=colors.text_primary, text_muted=colors.text_secondary,
            hover_background=colors.surface_hover,
            active_background=colors.bg_tertiary, active_indicator=colors.accent,
            separator=colors.divider, width=232, item_height=38,
        ))
