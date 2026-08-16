from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QDialog, QDialogButtonBox,
    QLineEdit, QSpinBox, QFormLayout, QLabel, QHBoxLayout, QFrame
)

from src.gui.ios.components import (
    IOSNavBar, IOSSectionHeader, IOSCard, IOSSettingsRow,
    IOSSwitch, IOSValueLabel
)
from src.gui.ios.compat import is_tweak_compatible
from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_loader import (
    load_featureflags, load_internal, load_liquidglass, load_springboard
)


class TextInputDialog(QDialog):
    """iOS-style text input dialog"""
    def __init__(self, title: str, current_value: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel { color: #FFFFFF; font-size: 15px; }
            QLineEdit {
                background-color: #3b3b3b;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                padding: 12px 16px;
            }
            QPushButton {
                background-color: #007AFF;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
            }
            QPushButton:hover { background-color: #0066CC; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self.input = QLineEdit()
        self.input.setText(current_value)
        self.input.setPlaceholderText(QCoreApplication.translate("TextInputDialog", "Enter value..."))
        layout.addWidget(self.input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #0066CC; }
        """)
        layout.addWidget(buttons)

    def get_value(self) -> str:
        return self.input.text()


class NumberInputDialog(QDialog):
    """iOS-style number input dialog"""
    def __init__(self, title: str, current_value: int = 0, min_val: int = 0, max_val: int = 999, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #FFFFFF; font-size: 15px; }
            QSpinBox {
                background-color: #3b3b3b;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                padding: 12px 16px;
            }
            QSpinBox::up-button, QSpinBox::down-button { width: 0; }
            QPushButton {
                background-color: #007AFF;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #0066CC; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self.spin = QSpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(current_value)
        self.spin.setButtonSymbols(QSpinBox.NoButtons)
        self.spin.setStyleSheet("""
            QSpinBox {
                background-color: #3b3b3b;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                padding: 12px 16px;
            }
        """)
        layout.addWidget(self.spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #0066CC; }
        """)
        layout.addWidget(buttons)

    def get_value(self) -> int:
        return self.spin.value()


class IOSTweaksPage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = IOSNavBar(QCoreApplication.translate("IOSTweaksPage", "tweaks"), window=self.window)
        layout.addWidget(nav)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 32)
        content_layout.setSpacing(8)

        # Page header matching card background
        page_header = QFrame()
        page_header.setFixedHeight(56)
        page_header.setStyleSheet("background-color: #1C1C1E;")
        page_header_layout = QHBoxLayout(page_header)
        page_header_layout.setContentsMargins(16, 8, 16, 8)
        page_title = QLabel(QCoreApplication.translate("IOSTweaksPage", "Tweaks"), page_header)
        page_title.setStyleSheet("font-size: 17px; font-weight: 600; color: #FFFFFF;")
        page_header_layout.addWidget(page_title, 1, Qt.AlignCenter)
        content_layout.addWidget(page_header)

        # Load tweaks (idempotent) so the sections below actually populate
        load_featureflags()
        load_internal()
        load_liquidglass()
        load_springboard()

        try:
            device_ver = self.window.device_manager.get_current_device_version()
        except Exception:
            device_ver = ""
        try:
            model = self.window.device_manager.get_current_device_model() or ""
        except Exception:
            model = ""
        is_iphone = model.startswith("iPhone")

        def is_compatible(tweak_id: TweakID) -> bool:
            return is_tweak_compatible(tweak_id, device_ver, is_iphone)

        # Helper to create a switch row for boolean tweaks
        def make_switch(tweak_id: TweakID, title: str, show_value=False):
            if tweak_id not in tweaks:
                return
            if not is_compatible(tweak_id):
                return
            tweak = tweaks[tweak_id]
            card = IOSCard()
            row_layout = QHBoxLayout(card)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            label = QLabel(title)
            label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
            row_layout.addWidget(label, 1)

            value_label = None
            if show_value and hasattr(tweak, 'value') and tweak.value:
                value_label = IOSValueLabel(f"({tweak.value})")
                row_layout.addWidget(value_label)

            switch = IOSSwitch(tweak.enabled)
            switch.toggled.connect(lambda checked: tweak.set_enabled(checked))
            row_layout.addWidget(switch)

            content_layout.addWidget(card)

        # Helper for text input tweaks
        def make_text_input(tweak_id: TweakID, title: str, placeholder: str = ""):
            if tweak_id not in tweaks:
                return
            if not is_compatible(tweak_id):
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

        # Helper for number input tweaks
        def make_number_input(tweak_id: TweakID, title: str, min_val: int = 0, max_val: int = 999):
            if tweak_id not in tweaks:
                return
            if not is_compatible(tweak_id):
                return
            tweak = tweaks[tweak_id]
            card = IOSCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            row = IOSSettingsRow(title)
            current = 0
            if hasattr(tweak, 'value') and tweak.value:
                current = int(tweak.value) if tweak.value else 0
                row.setText(f"{title}  ({current})")
            row.clicked.connect(lambda: self._show_number_input_dialog(tweak_id, title, current, row, min_val, max_val))
            card_layout.addWidget(row)
            content_layout.addWidget(card)

        # Liquid Glass section
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("Nugget", "Liquid Glass")))
        make_switch(TweakID.ForceSolariumFallback, QCoreApplication.translate("Nugget", "Force Solarium Fallback"))
        make_switch(TweakID.IgnoreSolariumLinkedOnCheck, QCoreApplication.translate("IOSTweaksPage", "Ignore Solarium Linked-On Check"))
        make_switch(TweakID.ForceSolariumIntelligence, QCoreApplication.translate("IOSTweaksPage", "Force Solarium Intelligence"))
        make_switch(TweakID.ForceEnhancedSpeculars, QCoreApplication.translate("IOSTweaksPage", "Force Enhanced Speculars"))
        make_switch(TweakID.UISolariumFallback, QCoreApplication.translate("IOSTweaksPage", "UI Solarium Fallback"))
        make_switch(TweakID.IgnoreSolariumHardwareCheck, QCoreApplication.translate("IOSTweaksPage", "Ignore Solarium Hardware Check"))
        make_switch(TweakID.IgnoreSolariumOptOut, QCoreApplication.translate("IOSTweaksPage", "Ignore Solarium Opt-Out"))
        make_switch(TweakID.DisallowGlassButtons, QCoreApplication.translate("IOSTweaksPage", "Disallow Glass Buttons"))
        make_switch(TweakID.DisallowGlassLockScreen, QCoreApplication.translate("IOSTweaksPage", "Disallow Glass Lock Screen"))
        make_switch(TweakID.DisableSpecularEverywhere, QCoreApplication.translate("IOSTweaksPage", "Disable Specular Everywhere"))
        make_switch(TweakID.NoLiquidClock, QCoreApplication.translate("Nugget", "Disable Liquid Glass on LS Clock"))
        make_switch(TweakID.NoLiquidDock, QCoreApplication.translate("Nugget", "Disable Liquid Glass on Dock"))
        make_switch(TweakID.DisableSpecularMotion, QCoreApplication.translate("Nugget", "Disable Specular Motion"))
        make_switch(TweakID.DisableOuterRefraction, QCoreApplication.translate("Nugget", "Disable Outer Refraction"))
        make_switch(TweakID.DisableSolariumHDR, QCoreApplication.translate("Nugget", "Disable Solarium HDR"))

        # SpringBoard section
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSTweaksPage", "SpringBoard")))
        make_text_input(TweakID.LockScreenFootnote, QCoreApplication.translate("Nugget", "Lock Screen Footnote Text"))
        make_switch(TweakID.WatchOSCompatibility, QCoreApplication.translate("Nugget", "Allow pairing with any watchOS version"))
        make_switch(TweakID.AirDropDisableTimeLimit, QCoreApplication.translate("Nugget", "Disable AirDrop Time Limit for Everyone Option"))
        make_switch(TweakID.SBDontLockAfterCrash, QCoreApplication.translate("Nugget", "Disable Lock After Respring"))
        make_switch(TweakID.SBDontDimOrLockOnAC, QCoreApplication.translate("Nugget", "Disable Screen Dimming While Charging"))
        make_switch(TweakID.SBHideLowPowerAlerts, QCoreApplication.translate("Nugget", "Disable Low Battery Alerts"))
        make_switch(TweakID.SBHideACPower, QCoreApplication.translate("Nugget", "Hide AC Power on Lock Screen"))
        make_switch(TweakID.SBNeverBreadcrumb, QCoreApplication.translate("Nugget", "Disable Breadcrumbs"))
        make_switch(TweakID.SBShowSupervisionTextOnLockScreen, QCoreApplication.translate("Nugget", "Show Supervision Text on Lock Screen"))
        make_switch(TweakID.AirplaySupport, QCoreApplication.translate("Nugget", "Enable AirPlay support for Stage Manager"))
        make_number_input(TweakID.SBMinimumLockscreenIdleTime, QCoreApplication.translate("Nugget", "Auto‑Lock (Lock Screen)"), 0, 600)
        make_switch(TweakID.SBAlwaysShowSystemApertureInSnapshots, QCoreApplication.translate("Nugget", "Show Dynamic Island in Screenshots"))
        make_switch(TweakID.HideDICompletely, QCoreApplication.translate("Nugget", "Hide Dynamic Island Completely"))
        make_switch(TweakID.SBShowAuthenticationEngineeringUI, QCoreApplication.translate("Nugget", "Show Red/Green Authentication Line on Lock Screen"))
        make_switch(TweakID.UseFloatingTabBar, QCoreApplication.translate("Nugget", "Disable Floating Tab Bar"))

        # Internal Options section
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("Nugget", "Internal Options")))
        make_switch(TweakID.SBBuildNumber, QCoreApplication.translate("Nugget", "Show Build Version in Status Bar"))
        make_switch(TweakID.RTL, QCoreApplication.translate("Nugget", "Force Right-to-Left Layout"))
        make_switch(TweakID.LTR, QCoreApplication.translate("Nugget", "Force Left-to-Right Layout"))
        make_switch(TweakID.SBIconVisibility, QCoreApplication.translate("Nugget", "Show Hidden Icons on Home Screen"))
        make_switch(TweakID.iMessageDiagnosticsEnabled, QCoreApplication.translate("Nugget", "iMessage Debugging"))
        make_switch(TweakID.IDSDiagnosticsEnabled, QCoreApplication.translate("Nugget", "Continuity Debugging"))
        make_switch(TweakID.VCDiagnosticsEnabled, QCoreApplication.translate("Nugget", "FaceTime Debugging"))
        make_switch(TweakID.AccessoryDeveloperEnabled, QCoreApplication.translate("Nugget", "Show Accessory Developer Settings"))
        make_switch(TweakID.DisableSecondsHand, QCoreApplication.translate("Nugget", "Disable Clock Icon Seconds Hand"))
        make_switch(TweakID.DisableSearchingWebsites, QCoreApplication.translate("Nugget", "Disable Spotlight Searching in Websites"))
        make_switch(TweakID.ShowButtonHints, QCoreApplication.translate("Nugget", "Show Hardware Button Hints in Screenshots"))
        make_switch(TweakID.AppStoreDebug, QCoreApplication.translate("Nugget", "App Store Debug Gesture"))
        make_switch(TweakID.NotesDebugMode, QCoreApplication.translate("Nugget", "Notes Debug Mode"))
        make_switch(TweakID.BKDigitizerVisualizeTouches, QCoreApplication.translate("Nugget", "Show Touches With Debug Info"))
        make_switch(TweakID.BKHideAppleLogoOnLaunch, QCoreApplication.translate("Nugget", "Hide Respring Icon"))
        make_switch(TweakID.EnableWakeGestureHaptic, QCoreApplication.translate("Nugget", "Vibrate on Raise-to-Wake"))
        make_switch(TweakID.PlaySoundOnPaste, QCoreApplication.translate("Nugget", "Play Sound on Paste"))
        make_switch(TweakID.AnnounceAllPastes, QCoreApplication.translate("Nugget", "Show Notifications for System Pastes"))

        # Risky / Advanced
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("Nugget", "Risky Options")))
        make_switch(TweakID.DisableOTAFile, QCoreApplication.translate("Nugget", "Disable OTA Updates (file)"))

        content_layout.addStretch()

    def _show_text_input_dialog(self, tweak_id: TweakID, title: str, current: str, row: IOSSettingsRow):
        dialog = TextInputDialog(title, current, self)
        if dialog.exec() == QDialog.Accepted:
            value = dialog.get_value()
            if value:
                tweaks[tweak_id].set_value(value, toggle_enabled=True)
                row.setText(f"{title}  ({value})")

    def _show_number_input_dialog(self, tweak_id: TweakID, title: str, current: int, row: IOSSettingsRow, min_val: int, max_val: int):
        dialog = NumberInputDialog(title, current, min_val, max_val, self)
        if dialog.exec() == QDialog.Accepted:
            value = dialog.get_value()
            tweaks[tweak_id].set_value(value, toggle_enabled=True)
            row.setText(f"{title}  ({value})")
