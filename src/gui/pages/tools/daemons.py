from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget
from src.gui.ios.daemons import IOSDaemonsContent


class DaemonsPage(Page):
    def __init__(self, ui: Ui_Nugget, window):
        super().__init__()
        self.ui = ui
        self.window = window
        self._content = None

    def load_page(self):
        if self._content is not None:
            return

        self.ui.daemonsScrollArea.setStyleSheet(
            "background-color: #1e1e1e; border: none;")
        self._content = IOSDaemonsContent(
            self.window, self.ui.daemonsScrollContent)
        self.ui.daemonsScrollLayout.addWidget(self._content)

    def refresh(self):
        if self._content is not None:
            self._content.refresh_from_tweaks()
