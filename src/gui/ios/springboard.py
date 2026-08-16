from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QLabel, QDialog

from src.gui.ios.components import IOSNavBar, IOSSectionHeader, IOSCard, IOSSwitch, IOSSettingsRow
from src.gui.ios.compat import is_tweak_compatible
from src.gui.ios.tweaks import TextInputDialog
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_loader import load_springboard


class IOSSpringboardPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = IOSNavBar(QCoreApplication.translate("Nugget", "Springboard Options"), window=self.window)
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

        try:
            device_ver = self.window.device_manager.get_current_device_version()
        except Exception:
            device_ver = ""
        try:
            model = self.window.device_manager.get_current_device_model() or ""
        except Exception:
            model = ""
        is_iphone = model.startswith("iPhone")

        # Helper to create switch row (skips if tweak not loaded or incompatible)
        def make_switch(tweak_id: TweakID, title: str):
            if tweak_id not in tweaks:
                return
            if not is_tweak_compatible(tweak_id, device_ver, is_iphone):
                return
            tweak = tweaks[tweak_id]
            card = IOSCard()
            row_layout = QHBoxLayout(card)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            label = QLabel(title)
            label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
            row_layout.addWidget(label, 1)

            switch = IOSSwitch(tweak.enabled)
            switch.toggled.connect(lambda checked: tweak.set_enabled(checked))
            row_layout.addWidget(switch)

            content_layout.addWidget(card)

        # Helper to create text input row (skips if tweak not loaded or incompatible)
        def make_text_input(tweak_id: TweakID, title: str):
            if tweak_id not in tweaks:
                return
            if not is_tweak_compatible(tweak_id, device_ver, is_iphone):
                return
            tweak = tweaks[tweak_id]
            card = IOSCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            row = IOSSettingsRow(title)
            current = ""
            if hasattr(tweak, 'value') and tweak.value:
                current = str(tweak.value)
                row.setText(f"{title}  ({current})")
            row.clicked.connect(lambda: self._show_text_input_dialog(tweak_id, title, current, row))
            card_layout.addWidget(row)
            content_layout.addWidget(card)

        # Lock Screen
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSSpringboardPage", "Lock Screen")))
        make_text_input(TweakID.LockScreenFootnote, QCoreApplication.translate("Nugget", "Lock Screen Footnote Text"))
        make_switch(TweakID.WatchOSCompatibility, QCoreApplication.translate("Nugget", "Allow pairing with any watchOS version"))
        make_switch(TweakID.SBDontLockAfterCrash, QCoreApplication.translate("Nugget", "Disable Lock After Respring"))
        make_switch(TweakID.SBDontDimOrLockOnAC, QCoreApplication.translate("Nugget", "Disable Screen Dimming While Charging"))
        make_switch(TweakID.SBHideLowPowerAlerts, QCoreApplication.translate("Nugget", "Disable Low Battery Alerts"))
        make_switch(TweakID.SBHideACPower, QCoreApplication.translate("Nugget", "Hide AC Power on Lock Screen"))
        make_switch(TweakID.SBNeverBreadcrumb, QCoreApplication.translate("Nugget", "Disable Breadcrumbs"))
        make_switch(TweakID.SBShowSupervisionTextOnLockScreen, QCoreApplication.translate("Nugget", "Show Supervision Text on Lock Screen"))

        # Dynamic Island
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSSpringboardPage", "Dynamic Island")))
        make_switch(TweakID.SBAlwaysShowSystemApertureInSnapshots, QCoreApplication.translate("Nugget", "Show Dynamic Island in Screenshots"))
        make_switch(TweakID.HideDICompletely, QCoreApplication.translate("Nugget", "Hide Dynamic Island Completely"))

        # UI Tweaks
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSSpringboardPage", "UI Tweaks")))
        make_switch(TweakID.AirplaySupport, QCoreApplication.translate("Nugget", "Enable AirPlay support for Stage Manager"))
        make_switch(TweakID.SBMinimumLockscreenIdleTime, QCoreApplication.translate("Nugget", "Auto‑Lock (Lock Screen)"))
        make_switch(TweakID.SBShowAuthenticationEngineeringUI, QCoreApplication.translate("Nugget", "Show Red/Green Authentication Line on Lock Screen"))
        make_switch(TweakID.UseFloatingTabBar, QCoreApplication.translate("Nugget", "Disable Floating Tab Bar"))

        # AirDrop
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSSpringboardPage", "AirDrop")))
        make_switch(TweakID.AirDropDisableTimeLimit, QCoreApplication.translate("Nugget", "Disable AirDrop Time Limit for Everyone Option"))

        content_layout.addStretch()

        # Load springboard tweaks
        load_springboard()

    def _show_text_input_dialog(self, tweak_id: TweakID, title: str, current: str, row: IOSSettingsRow):
        dialog = TextInputDialog(title, current, self)
        if dialog.exec() == QDialog.Accepted:
            value = dialog.get_value()
            if value:
                tweaks[tweak_id].set_value(value, toggle_enabled=True)
                row.setText(f"{title}  ({value})")