from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QLabel, QMessageBox

from src.gui.ios.components import IOSSectionHeader, IOSSwitch, install_instant_tooltip
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_loader import load_daemons
from src.tweaks.daemons_tweak import (
    Daemon,
    DaemonCategory,
    RECOMMENDED_ANALYTICS,
    daemon_category,
    daemon_title,
    daemon_description,
)


class IOSDaemonsContent(QWidget):
    """iOS-style daemons controls, usable inside any scroll area or page."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window

        # Ensure daemons tweaks are loaded
        load_daemons()

        self.daemons_tweak = tweaks[TweakID.Daemons]
        self.screen_time_tweak = tweaks.get(TweakID.ClearScreenTimeAgentPlist)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 32)
        layout.setSpacing(8)

        # Master enable switch
        layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Daemons to Disable")
        ))
        master_card = QWidget()
        master_row = QHBoxLayout(master_card)
        master_row.setContentsMargins(16, 10, 16, 10)
        master_row.setSpacing(12)
        master_label = QLabel(QCoreApplication.translate("Nugget", "Enable Daemon Modifications"))
        master_label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        master_help = QCoreApplication.translate(
            "Nugget", "Master switch for the whole Daemons feature. When OFF, none of the "
            "daemon toggles below are applied. When ON, every daemon you toggle gets disabled "
            "on-device.\n\nTip: keep problematic systems enabled (Backboardd, SpringBoard, "
            "Telephony, Network and similar) and only disable telemetry, tracking and logging "
            "daemons.")
        master_card.setToolTip(master_help)
        master_label.setToolTip(master_help)
        install_instant_tooltip(master_card)
        install_instant_tooltip(master_label)
        master_row.addWidget(master_label, 1)
        self.master_switch = IOSSwitch(self.daemons_tweak.enabled)
        self.master_switch.setToolTip(master_help)
        install_instant_tooltip(self.master_switch)
        self.master_switch.toggled.connect(self._on_master_toggled)
        master_row.addWidget(self.master_switch)
        layout.addWidget(master_card)

        # Recommended: select all analytics/telemetry daemons in one tap
        self.recommended_card, self.recommended_switch = self._make_recommended_switch(layout)

        self.daemon_cards = []
        self.daemon_switches = []

        # "Analytics, Data Tracking & Logging" combined section, with a Select All toggle.
        adl_categories = [
            DaemonCategory.LOGGING,
            DaemonCategory.ANALYTICS,
            DaemonCategory.TRACKING,
        ]
        adl_items = [d for d in Daemon if daemon_category(d) in adl_categories]
        layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Analytics, Data Tracking & Logging")
        ))
        self.adl_select_card, self.adl_select_switch = self._make_section_select_switch(
            layout,
            adl_items,
            QCoreApplication.translate("Nugget", "Select all analytics, tracking & logging daemons"))
        self.adl_select_items = adl_items
        for daemon in adl_items:
            card, switch = self._make_daemon_switch(layout, daemon_title(daemon), daemon)
            self.daemon_cards.append(card)
            self.daemon_switches.append((daemon, switch))

        other_items = [d for d in Daemon if daemon_category(d) is DaemonCategory.OTHER]
        if other_items:
            layout.addWidget(IOSSectionHeader(
                QCoreApplication.translate("Nugget", "Other")
            ))
            for daemon in other_items:
                card, switch = self._make_daemon_switch(layout, daemon_title(daemon), daemon)
                self.daemon_cards.append(card)
                self.daemon_switches.append((daemon, switch))

        # Screen Time
        layout.addWidget(IOSSectionHeader(
            QCoreApplication.translate("Nugget", "Disable Screen Time Agent")
        ))
        if self.screen_time_tweak is not None:
            card = QWidget()
            row_layout = QHBoxLayout(card)
            row_layout.setContentsMargins(16, 10, 16, 10)
            row_layout.setSpacing(12)
            label = QLabel(QCoreApplication.translate("Nugget", "Clear ScreenTimeAgent.plist file"))
            label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
            st_help = QCoreApplication.translate(
                "Nugget", "Deletes the ScreenTimeAgent.plist file so Screen Time limits stop being enforced.")
            card.setToolTip(st_help)
            label.setToolTip(st_help)
            install_instant_tooltip(card)
            install_instant_tooltip(label)
            row_layout.addWidget(label, 1)
            self.screen_time_switch = IOSSwitch(self.screen_time_tweak.enabled)
            self.screen_time_switch.setToolTip(st_help)
            install_instant_tooltip(self.screen_time_switch)
            self.screen_time_switch.toggled.connect(self.screen_time_tweak.set_enabled)
            row_layout.addWidget(self.screen_time_switch)
            layout.addWidget(card)

        self._update_daemons_enabled()
        layout.addStretch()

    def _make_daemon_switch(self, layout, title: str, daemon: Daemon):
        card = QWidget()
        row_layout = QHBoxLayout(card)
        row_layout.setContentsMargins(16, 10, 16, 10)
        row_layout.setSpacing(12)

        description = daemon_description(daemon)
        card.setToolTip(description)
        install_instant_tooltip(card)

        label = QLabel(title)
        label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        label.setToolTip(description)
        install_instant_tooltip(label)
        row_layout.addWidget(label, 1)

        value = self.daemons_tweak.value.get(daemon.value[0], False) if self.daemons_tweak.value else False
        switch = IOSSwitch(value)
        switch.setToolTip(description)
        install_instant_tooltip(switch)
        switch.toggled.connect(
            lambda checked, d=daemon: self._on_daemon_toggled(d, checked)
        )
        row_layout.addWidget(switch)

        layout.addWidget(card)
        return card, switch

    def _make_recommended_switch(self, layout):
        """Recommended button that toggles every analytics daemon at once."""
        card = QWidget()
        row_layout = QHBoxLayout(card)
        row_layout.setContentsMargins(16, 10, 16, 10)
        row_layout.setSpacing(12)

        label = QLabel(QCoreApplication.translate(
            "Nugget", "Recommended (analytics, tracking & logging)"))
        label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600;")
        label.setToolTip(QCoreApplication.translate(
            "Nugget", "Enable the recommended set of telemetry, analytics, and tracking daemons at once."))
        install_instant_tooltip(label)
        row_layout.addWidget(label, 1)

        value = all(
            self.daemons_tweak.value.get(d.value[0], False)
            if self.daemons_tweak.value else False
            for d in RECOMMENDED_ANALYTICS)
        switch = IOSSwitch(value)
        switch.setToolTip(QCoreApplication.translate(
            "Nugget", "Enable the recommended set of telemetry, analytics, and tracking daemons at once."))
        install_instant_tooltip(switch)
        switch.toggled.connect(self._on_recommended_toggled)
        row_layout.addWidget(switch)

        layout.addWidget(card)
        return card, switch

    def _on_recommended_toggled(self, checked: bool):
        for daemon in RECOMMENDED_ANALYTICS:
            self.daemons_tweak.set_multiple_values(daemon.value, value=checked)
            for d, sw in self.daemon_switches:
                if d is daemon:
                    sw.blockSignals(True)
                    sw.setChecked(checked)
                    sw.blockSignals(False)
                    break
        if checked:
            self.master_switch.setChecked(True)

    def _make_section_select_switch(self, layout, daemons, label_text):
        """Select All toggle for a whole section of daemons."""
        card = QWidget()
        row_layout = QHBoxLayout(card)
        row_layout.setContentsMargins(16, 10, 16, 10)
        row_layout.setSpacing(12)

        label = QLabel(label_text)
        label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600;")
        select_help = QCoreApplication.translate(
            "Nugget", "Toggle every daemon in this section at once.")
        label.setToolTip(select_help)
        install_instant_tooltip(label)
        row_layout.addWidget(label, 1)

        daemons = list(daemons)
        value = all(
            self.daemons_tweak.value.get(d.value[0], False)
            if self.daemons_tweak.value else False
            for d in daemons
        ) if daemons else False
        switch = IOSSwitch(value)
        switch.setToolTip(select_help)
        install_instant_tooltip(switch)
        switch.toggled.connect(lambda checked, ds=daemons: self._on_section_select_toggled(ds, checked))
        row_layout.addWidget(switch)

        layout.addWidget(card)
        return card, switch

    def _on_section_select_toggled(self, daemons, checked: bool):
        for daemon in daemons:
            self.daemons_tweak.set_multiple_values(daemon.value, value=checked)
            for d, sw in self.daemon_switches:
                if d is daemon:
                    sw.blockSignals(True)
                    sw.setChecked(checked)
                    sw.blockSignals(False)
                    break
        if checked:
            self.master_switch.setChecked(True)

    def _section_all_on(self, daemons) -> bool:
        value = self.daemons_tweak.value
        if not value:
            return False
        return all(value.get(d.value[0], False) for d in daemons)

    def _on_master_toggled(self, checked: bool):
        self.daemons_tweak.set_enabled(checked)
        self._update_daemons_enabled()

    def _on_daemon_toggled(self, daemon: Daemon, checked: bool):
        self.daemons_tweak.set_multiple_values(daemon.value, value=checked)
        if checked:
            self.master_switch.setChecked(True)
            if daemon is Daemon.Location:
                self._warn_location_daemon()

    def _warn_location_daemon(self):
        """Location Services daemon keeps PosterBoard alive on iPhone 14."""
        from src.devicemanagement.data_singleton import DataSingleton
        current = DataSingleton().current_device
        model = current.model if current is not None else ""
        if not model.startswith("iPhone14,"):
            return
        QMessageBox.warning(
            self,
            QCoreApplication.translate("Nugget", "Wallpaper Risk on iPhone 14"),
            QCoreApplication.translate(
                "Nugget",
                "Disabling Location Services has been reported to break wallpapers "
                "(PosterBoard) on iPhone 14. If your wallpaper disappears after "
                "applying, re-enable this daemon and apply again."))

    def _update_daemons_enabled(self):
        enabled = self.daemons_tweak.enabled
        for card in self.daemon_cards:
            card.setEnabled(enabled)
        for attr in ('recommended_card', 'adl_select_card'):
            card = getattr(self, attr, None)
            if card is not None:
                card.setEnabled(enabled)

    def _recommended_all_on(self) -> bool:
        value = self.daemons_tweak.value
        if not value:
            return False
        return all(value.get(d.value[0], False) for d in RECOMMENDED_ANALYTICS)

    def refresh_from_tweaks(self):
        """Resync every switch with the current tweak state."""
        self.master_switch.blockSignals(True)
        self.master_switch.setChecked(self.daemons_tweak.enabled)
        self.master_switch.blockSignals(False)
        self._update_daemons_enabled()

        for daemon, switch in self.daemon_switches:
            value = self.daemons_tweak.value.get(daemon.value[0], False) if self.daemons_tweak.value else False
            switch.blockSignals(True)
            switch.setChecked(value)
            switch.blockSignals(False)

        recommended_switch = getattr(self, 'recommended_switch', None)
        if recommended_switch is not None:
            recommended_switch.blockSignals(True)
            recommended_switch.setChecked(self._recommended_all_on())
            recommended_switch.blockSignals(False)

        adl_switch = getattr(self, 'adl_select_switch', None)
        adl_items = getattr(self, 'adl_select_items', [])
        if adl_switch is not None:
            adl_switch.blockSignals(True)
            adl_switch.setChecked(self._section_all_on(adl_items))
            adl_switch.blockSignals(False)

        screen_time_switch = getattr(self, 'screen_time_switch', None)
        if screen_time_switch is not None:
            screen_time_switch.blockSignals(True)
            screen_time_switch.setChecked(self.screen_time_tweak.enabled)
            screen_time_switch.blockSignals(False)


class IOSDaemonsPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        self.content = IOSDaemonsContent(window, self)
        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def refresh_from_tweaks(self):
        self.content.refresh_from_tweaks()
