from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QLabel

from src.gui.ios.components import IOSNavBar, IOSSectionHeader, IOSCard, IOSSwitch
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_loader import load_daemons
from src.tweaks.daemons_tweak import Daemon


class IOSDaemonsPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        # Ensure daemons tweaks are loaded
        load_daemons()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = IOSNavBar(QCoreApplication.translate("IOSDaemonsPage", "Daemons"), window=self.window)
        layout.addWidget(nav)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 32)
        content_layout.setSpacing(8)

        self.daemons_tweak = tweaks[TweakID.Daemons]

        # Master enable switch
        content_layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("IOSDaemonsPage", "Daemons to Disable")
        ))
        master_card = IOSCard()
        master_row = QHBoxLayout(master_card)
        master_row.setContentsMargins(16, 10, 16, 10)
        master_row.setSpacing(12)
        master_label = QLabel(QCoreApplication.translate("IOSDaemonsPage", "Enable Daemon Modifications"))
        master_label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        master_row.addWidget(master_label, 1)
        self.master_switch = IOSSwitch(self.daemons_tweak.enabled)
        self.master_switch.toggled.connect(self._on_master_toggled)
        master_row.addWidget(self.master_switch)
        content_layout.addWidget(master_card)

        self.daemon_cards = []
        for title, daemon in [
            (QCoreApplication.translate("Nugget", "Disable thermalmonitord"), Daemon.thermalmonitord),
            (QCoreApplication.translate("Nugget", "Disable OTA"), Daemon.OTA),
            (QCoreApplication.translate("Nugget", "Disable UsageTrackingAgent"), Daemon.UsageTrackingAgent),
            (QCoreApplication.translate("Nugget", "Disable Game Center"), Daemon.GameCenter),
            (QCoreApplication.translate("Nugget", "Disable Screen Time Agent"), Daemon.ScreenTime),
            (QCoreApplication.translate("Nugget", "Disable Logs, Dumps, and Crash Reports"), Daemon.CrashReports),
            (QCoreApplication.translate("Nugget", "Disable ATWAKEUP"), Daemon.ATWAKEUP),
            (QCoreApplication.translate("Nugget", "Disable Tips Services"), Daemon.Tips),
            (QCoreApplication.translate("Nugget", "VPN Icon"), Daemon.VPN),
            (QCoreApplication.translate("Nugget", "Disable Chinese WLAN Service"), Daemon.ChineseLAN),
            (QCoreApplication.translate("Nugget", "Disable HealthKit"), Daemon.HealthKit),
            (QCoreApplication.translate("Nugget", "Disable AirPrint"), Daemon.AirPrint),
            (QCoreApplication.translate("Nugget", "Disable Assistive Touch"), Daemon.AssistiveTouch),
            (QCoreApplication.translate("Nugget", "Disable iCloud"), Daemon.iCloud),
            (QCoreApplication.translate("Nugget", "Disable Internet Tethering (Hotspot)"), Daemon.InternetTethering),
            (QCoreApplication.translate("Nugget", "Disable Passbook"), Daemon.PassBook),
            (QCoreApplication.translate("Nugget", "Disable Spotlight"), Daemon.Spotlight),
            (QCoreApplication.translate("Nugget", "Voice Control Icon"), Daemon.VoiceControl),
            (QCoreApplication.translate("Nugget", "Disable NanoTimeKit (Apple Watch Face Sync)"), Daemon.NanoTimeKit),
            (QCoreApplication.translate("Nugget", "Disable System Diagnostics"), Daemon.Diagnostics),
            (QCoreApplication.translate("IOSDaemonsPage", "Follow Up"), Daemon.FollowUp),
            (QCoreApplication.translate("IOSDaemonsPage", "Location Services"), Daemon.Location),
        ]:
            self.daemon_cards.append(self._make_daemon_switch(content_layout, title, daemon))

        # Screen Time
        content_layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Disable Screen Time Agent")
        ))
        self.screen_time_tweak = tweaks.get(TweakID.ClearScreenTimeAgentPlist)
        if self.screen_time_tweak is not None:
            card = IOSCard()
            row_layout = QHBoxLayout(card)
            row_layout.setContentsMargins(16, 10, 16, 10)
            row_layout.setSpacing(12)
            label = QLabel(QCoreApplication.translate("Nugget", "Clear ScreenTimeAgent.plist file"))
            label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
            row_layout.addWidget(label, 1)
            switch = IOSSwitch(self.screen_time_tweak.enabled)
            switch.toggled.connect(self.screen_time_tweak.set_enabled)
            row_layout.addWidget(switch)
            content_layout.addWidget(card)

        self._update_daemons_enabled()
        content_layout.addStretch()

    def _make_daemon_switch(self, content_layout, title: str, daemon: Daemon) -> IOSCard:
        card = IOSCard()
        row_layout = QHBoxLayout(card)
        row_layout.setContentsMargins(16, 10, 16, 10)
        row_layout.setSpacing(12)

        label = QLabel(title)
        label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        row_layout.addWidget(label, 1)

        value = self.daemons_tweak.value.get(daemon.value[0], False) if self.daemons_tweak.value else False
        switch = IOSSwitch(value)
        switch.toggled.connect(
            lambda checked, d=daemon: self._on_daemon_toggled(d, checked)
        )
        row_layout.addWidget(switch)

        content_layout.addWidget(card)
        return card

    def _on_master_toggled(self, checked: bool):
        self.daemons_tweak.set_enabled(checked)
        self._update_daemons_enabled()

    def _on_daemon_toggled(self, daemon: Daemon, checked: bool):
        self.daemons_tweak.set_multiple_values(daemon.value, value=checked)
        if checked:
            self.master_switch.setChecked(True)

    def _update_daemons_enabled(self):
        enabled = self.daemons_tweak.enabled
        for card in self.daemon_cards:
            card.setEnabled(enabled)
