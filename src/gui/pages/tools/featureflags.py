from ..page import Page
from src.qt.mainwindow_ui import Ui_Nugget

from src.tweaks.tweak_loader import load_featureflags
from src.tweaks.tweaks import tweaks, TweakID

class FeatureFlagsPage(Page):
    def __init__(self, ui: Ui_Nugget):
        super().__init__()
        self.ui = ui

    def load_page(self):
        self.ui.clockAnimChk.toggled.connect(self.on_clockAnimChk_toggled)
        self.ui.lockscreenChk.toggled.connect(self.on_lockscreenChk_clicked)
        self.ui.kioskModeChk.toggled.connect(self.on_kioskModeChk_toggled)
        self.ui.solariumFFChk.toggled.connect(self.on_solariumFFChk_toggled)
        self.ui.photosLGFFChk.toggled.connect(self.on_photosLGFFChk_toggled)
        self.ui.shareSheetLGFFChk.toggled.connect(self.on_shareSheetLGFFChk_toggled)

        # hide the removed features (mobilegestalt / eligibility era, iOS 26.2+)
        for widget_name in ("createFFFolderChk", "createEligFolderChk", "photosChk", "aiChk"):
            widget = getattr(self.ui, widget_name, None)
            if widget is not None:
                widget.hide()

        load_featureflags()

    ## ACTIONS
    def on_clockAnimChk_toggled(self, checked: bool):
        tweaks[TweakID.ClockAnim].set_enabled(checked)
    def on_lockscreenChk_clicked(self, checked: bool):
        tweaks[TweakID.Lockscreen].set_enabled(checked)

    def on_kioskModeChk_toggled(self, checked: bool):
        tweaks[TweakID.KioskMode].set_enabled(checked)
    def on_solariumFFChk_toggled(self, checked: bool):
        tweaks[TweakID.SolariumFFSwiftUI].set_enabled(checked)
        tweaks[TweakID.SolariumFFSpringBoard].set_enabled(checked)
        tweaks[TweakID.SolariumFFIconServices].set_enabled(checked)
    def on_photosLGFFChk_toggled(self, checked: bool):
        tweaks[TweakID.SolariumFFDocumentCamera].set_enabled(checked)
        tweaks[TweakID.SolariumFFPhotos].set_enabled(checked)
        tweaks[TweakID.SolariumFFAppleMediaServices].set_enabled(checked)
    def on_shareSheetLGFFChk_toggled(self, checked: bool):
        tweaks[TweakID.SolariumFFSharing].set_enabled(checked)
        tweaks[TweakID.SolariumFFMail].set_enabled(checked)
