from PySide6 import QtCore, QtWidgets
from typing import Optional

from src.qt.mainwindow_ui import Ui_Nugget
import src.gui.pages as Pages

from src.controllers.web_request_handler import is_update_available
from src.controllers.translator import Translator
import src.controllers.video_handler as video_handler
from src.controllers.preset_manager import PresetManager

from src.devicemanagement.constants import Version, LEGACY_SUPPORT_ENABLED
from src.devicemanagement.device_manager import DeviceManager

from src.gui.dialogs import UpdateAppDialog, AboutProgramDialog
from src.gui.dialogs.reset_dialog import ResetDialog
from src.gui.thread_workers.apply_worker import ApplyThread, ApplyAlertMessage, RefreshDevicesThread, set_sudo_pwd, get_sudo_pwd
from src.gui.pages.pages_list import Page

from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_classes import set_tweak_change_callback
from src.gui.version import App_Version, App_Build

from src.gui.ios.theme_manager import ThemeManager
from src.gui.ios.home import IOSHomePage
from src.gui.ios.tweaks import IOSTweaksPage
from src.gui.ios.posterboard import IOSPosterboardPage
from src.gui.ios.daemons import IOSDaemonsPage
from src.gui.ios.settings import IOSSettingsPage
from src.gui.ios.statusbar import IOSStatusBarPage

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, device_manager: DeviceManager, translator: Translator):
        super(MainWindow, self).__init__()
        self.device_manager = device_manager
        self.translator = translator
        self.settings = self.translator.settings
        self.ui = Ui_Nugget()
        self.ui.setupUi(self)
        self.noneText = self.tr("None")
        self.apply_in_progress = False
        self.refresh_in_progress = False
        self.threadpool = QtCore.QThreadPool()

        self.preset_manager = PresetManager()
        self._preset_autosave_pending = False

        self.loadSettings()
        self._load_last_preset()
        self._register_tweak_autosave()

        self.initial_load = True

        # hide every page
        self.ui.posterboardPageBtn.hide()
        self.ui.templatePageBtn.hide()
        self.ui.euEnablerPageBtn.hide()
        self.ui.enableiPadOSChk.hide()
        self.ui.ipadOSAlphaWarningLbl.hide()
        self.ui.statusBarPageBtn.hide()
        self.ui.springboardOptionsPageBtn.hide()
        self.ui.internalOptionsPageBtn.hide()
        self.ui.daemonsPageBtn.hide()
        self.ui.templatesPageBtn.hide()
        self.ui.passcodePageBtn.hide()
        self.ui.tweaksPageBtn.hide()
        self.ui.applyPageBtn.hide()
        self.ui.sidebarDiv1.hide()
        self.ui.sidebarDiv2.hide()

        # pre-load the pages
        self.pages = {
            Page.Home: Pages.Home(window=self, ui=self.ui),
            Page.Posterboard: Pages.Posterboard(window=self, ui=self.ui),
            Page.StatusBar: Pages.StatusBar(ui=self.ui),
            Page.Springboard: Pages.Springboard(ui=self.ui),
            Page.InternalOptions: Pages.Internal(ui=self.ui),
            Page.LiquidGlass: Pages.LiquidGlass(ui=self.ui),
            Page.Daemons: Pages.Daemons(ui=self.ui),
            Page.Templates: Pages.Templates(window=self, ui=self.ui),
            Page.Passcode: Pages.Passcode(window=self, ui=self.ui),
            Page.Settings: Pages.Settings(window=self, ui=self.ui)
        }

        # theme manager wraps the classic UI and the iOS stack
        self.theme_manager = ThemeManager(self)

        # build the iOS-style pages stack
        # 0 = home, 1 = tweaks, 2 = posterboard, 3 = springboard, 4 = daemons, 5 = settings, 6 = statusbar, 7 = passcode
        self.ios_pages = QtWidgets.QStackedWidget(self)
        self.ios_pages.setStyleSheet("background-color: #1e1e1e;")
        self.ios_home = IOSHomePage(self)
        self.ios_tweaks = IOSTweaksPage(self)
        self.ios_posterboard = IOSPosterboardPage(self)
        self.ios_daemons = IOSDaemonsPage(self)
        self.ios_settings = IOSSettingsPage(self)
        self.ios_statusbar = IOSStatusBarPage(self)
        self.ios_pages.addWidget(self.ios_home)
        self.ios_pages.addWidget(self.ios_tweaks)
        self.ios_pages.addWidget(self.ios_posterboard)
        self.ios_pages.addWidget(self.ios_daemons)
        self.ios_pages.addWidget(self.ios_settings)
        self.ios_pages.addWidget(self.ios_statusbar)

        self.theme_manager.set_classic_widget(self.ui.centralwidget)
        self.theme_manager.set_ios_widget(self.ios_pages)
        self.setCentralWidget(self.theme_manager.stack)

        # Back navigation: ESC key and mouse back button go to the home page
        QtWidgets.QApplication.instance().installEventFilter(self)

        # Check for an update
        if is_update_available(App_Version, App_Build):
            # notify with prompt to download the new version from github
            UpdateAppDialog().exec()
        # Update the app version/build number label
        self.updateAppVersionLabel()
        self.pages[Page.Home].load()
        
        # Add About button next to title
        self.aboutBtn = QtWidgets.QToolButton()
        self.aboutBtn.setText(self.tr("About"))
        self.aboutBtn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.aboutBtn.setStyleSheet("""
            QToolButton {
                color: #8E8E93;
                font-size: 13px;
                background: none;
                border: none;
                padding: 4px 8px;
            }
            QToolButton:hover {
                color: #007AFF;
            }
        """)
        self.aboutBtn.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.aboutBtn.clicked.connect(self.show_about_dialog)
        
        # Add to the title bar layout
        title_layout = self.ui.horizontalLayout_15
        title_layout.addWidget(self.aboutBtn)
        
        ## DEVICE BAR
        self.refresh_devices()

        self.ui.refreshBtn.clicked.connect(self.refresh_devices)
        self.ui.devicePicker.currentIndexChanged.connect(self.change_selected_device)

        # disable video features if OpenCV isn't working properly
        if not video_handler.cv2_successful:
            self.ui.videoPageBtn.hide()

        ## SIDE BAR ACTIONS
        self.ui.homePageBtn.clicked.connect(self.on_homePageBtn_clicked)
        self.ui.statusBarPageBtn.clicked.connect(self.on_statusBarPageBtn_clicked)
        self.ui.springboardOptionsPageBtn.clicked.connect(self.on_springboardOptionsPageBtn_clicked)
        self.ui.internalOptionsPageBtn.clicked.connect(self.on_internalOptionsPageBtn_clicked)
        self.ui.liquidGlassPageBtn.clicked.connect(self.on_liquidGlassPageBtn_clicked)
        self.ui.daemonsPageBtn.clicked.connect(self.on_daemonsPageBtn_clicked)
        self.ui.posterboardPageBtn.clicked.connect(self.on_posterboardPageBtn_clicked)
        self.ui.templatesPageBtn.clicked.connect(self.on_templatesPageBtn_clicked)
        self.ui.tweaksPageBtn.clicked.connect(self.on_tweaksPageBtn_clicked)
        self.ui.applyPageBtn.clicked.connect(self.on_applyPageBtn_clicked)
        self.ui.settingsPageBtn.clicked.connect(self.on_settingsPageBtn_clicked)

        ## APPLY PAGE ACTIONS
        self.ui.applyTweaksBtn.clicked.connect(self.on_applyTweaksBtn_clicked)
        self.ui.removeTweaksBtn.clicked.connect(self.on_removeTweaksBtn_clicked)


    ## GENERAL INTERFACE FUNCTIONS
    def updateInterfaceForNewDevice(self):
        # update the home page
        self.pages[Page.Home].updatePhoneInfo()
    
    def updateAppVersionLabel(self):
        new_text: str = self.ui.appVersionLbl.text()
        version_str = App_Version
        if LEGACY_SUPPORT_ENABLED:
            version_str = f"{App_Version} (legacy)"
        new_text = new_text.replace("%VERSION", version_str)
        if App_Build > 0:
            new_text = new_text.replace("%BETATAG", f"(beta {App_Build})")
        else:
            new_text = new_text.replace("%BETATAG", "")
        self.ui.appVersionLbl.setText(new_text)


    ## DEVICE BAR FUNCTIONS
    @QtCore.Slot()
    def refresh_devices(self):
        if not self.refresh_in_progress:
            self.refresh_in_progress = True
            self.ui.refreshBtn.setDisabled(True)
            self.refresh_worker_thread = RefreshDevicesThread(manager=self.device_manager, settings=self.settings)
            self.refresh_worker_thread.alert.connect(self.alert_message)
            self.refresh_worker_thread.finished.connect(self.refresh_devices_finished)
            self.refresh_worker_thread.finished.connect(self.refresh_worker_thread.deleteLater)
            self.refresh_worker_thread.start()

    def warn_for_dev_beta(self):
        ver = self.device_manager.get_current_device_version()
        if ver == "":
            return
        if Version(ver) > Version("26.0") and not self.device_manager.get_current_device_build()[-1].isdigit():
            self.alert_message(ApplyAlertMessage(
                txt=self.tr("Warning: You are on iOS 26 beta.\n\nThis has been known to cause problems and potentially lead to bootloops.\n\nUse at your own risk!"),
                title="Warning", icon=QtWidgets.QMessageBox.Warning
            ), log_to_console=False)

    def update_pb_saved_ids_list(self):
        # update PosterBoard saved ids list
        self.ui.savedConfigIdsList.clear()
        saved_ids = tweaks[TweakID.PosterBoard].config_manager.saved_items
        if len(saved_ids) == 0:
            self.ui.savedConfigIdsList.setDisabled(True)
            self.ui.savedConfigIdsList.addItem("None")
        else:
            self.ui.savedConfigIdsList.setDisabled(False)
            self.ui.savedConfigIdsList.addItems([id.to_str() for id in saved_ids])

    def refresh_devices_finished(self):
        self.refresh_in_progress = False
        self.toggle_thread_btns(disabled=False)
        # clear the picker
        self.ui.devicePicker.clear()
        self.ui.restoreProgressBar.hide()

        if len(self.device_manager.devices) == 0:
            self.ui.devicePicker.setEnabled(False)
            self.ui.devicePicker.addItem(self.noneText)
            self.ui.pages.setCurrentIndex(Page.Home.value)
            self.ui.homePageBtn.setChecked(True)

            # hide all pages
            self.ui.sidebarDiv1.hide()

            self.ui.gestaltPageBtn.hide()
            self.ui.statusBarPageBtn.hide()
            self.ui.springboardOptionsPageBtn.hide()
            self.ui.internalOptionsPageBtn.hide()
            self.ui.daemonsPageBtn.hide()
            self.ui.templatesPageBtn.hide()
            self.ui.passcodePageBtn.hide()
            self.ui.posterboardPageBtn.hide()
            self.ui.tweaksPageBtn.hide()

            self.ui.sidebarDiv2.hide()
            self.ui.applyPageBtn.hide()
            self.ui.jjtechBtn.hide()
            self.ui.duyBtn.show()

            self.ui.resetPairBtn.hide()
            # mirror in the iOS UI: no device → no status bar card
            if hasattr(self, "ios_home"):
                self.ios_home.set_statusbar_visible(False)
        else:
            self.ui.devicePicker.setEnabled(True)
            # populate the ComboBox with device names
            for device in self.device_manager.devices:
                tag = " (@ USB)" if device.connected_via_usb else " (@ WiFi)"
                self.ui.devicePicker.addItem(f"{device.name}{tag}")
            
            # show all pages
            self.ui.sidebarDiv1.show()
            self.ui.statusBarPageBtn.show()
            self.ui.springboardOptionsPageBtn.show()
            self.ui.internalOptionsPageBtn.show()
            self.ui.daemonsPageBtn.show()
            self.ui.templatesPageBtn.show()
            self.ui.passcodePageBtn.hide()
            self.ui.posterboardPageBtn.show()
            self.ui.tweaksPageBtn.show()
            
            self.ui.sidebarDiv2.show()
            self.ui.applyPageBtn.show()

            self.ui.springboardOptionsPageContent.setDisabled(False)
            self.ui.internalOptionsPageContent.setDisabled(False)
            self.ui.advancedOptionsPageContent.setDisabled(False)
            self.ui.liquidGlassPageContent.setDisabled(False)
            self.ui.pbPages.setDisabled(False)

            self.ui.resetPairBtn.show()
        
        # update the selected device
        self.ui.devicePicker.setCurrentIndex(0)
        # keep the iOS home in sync
        self.ios_home.refresh_device_combo()
        self.ios_home.update_device_info()
        self.ios_home.update_status()

    def change_selected_device(self, index):
        if len(self.device_manager.devices) > 0:
            self.device_manager.set_current_device(index=index)
            # hide options that are for newer versions
            MinTweakVersions = {
                "no_patch": [self.ui.chooseGestaltBtn, self.ui.gestaltPageBtn, self.ui.gestaltLocationLbl, self.ui.gestaltLocationTitleLbl],
                "exploit": [("1.0", self.ui.regularDomainsLbl)],
                "17.4": [self.ui.supportsDIChk],
                "18.0": [self.ui.aodChk, self.ui.aodVibrancyChk, self.ui.iphone16SettingsChk],
                "26.0": [self.ui.liquidGlassPageBtn]
            }

            device_ver = Version(self.device_manager.data_singleton.current_device.version)
            patched: bool = self.device_manager.get_current_device_patched()
            # toggle option visibility for the minimum versions
            for version in MinTweakVersions.keys():
                if version == "exploit":
                    # disable if the exploit is not available
                    for pair in MinTweakVersions[version]:
                        if self.device_manager.data_singleton.current_device.has_exploit() and device_ver >= Version(pair[0]):
                            pair[1].show()
                        else:
                            pair[1].hide()
                elif version == "no_patch":
                    # hide patched version items
                    for view in MinTweakVersions[version]:
                        if patched:
                            view.hide()
                        else:
                            view.show()
                else:
                    # show views if the version is higher
                    parsed_ver = Version(version)
                    for view in MinTweakVersions[version]:
                        if device_ver >= parsed_ver:
                            view.show()
                        else:
                            view.hide()
            # The Status Bar override file is dropped by the iOS 27
            # safe-state-recovery wipe, so the whole feature is hidden on iOS 27+.
            if device_ver >= Version("27.0"):
                self.ui.statusBarPageBtn.hide()
            else:
                self.ui.statusBarPageBtn.show()
            # mirror the Status Bar gating in the iOS UI
            if hasattr(self, "ios_home"):
                self.ios_home.set_statusbar_visible(device_ver < Version("27.0"))

            # hide posterboard .aar video option on ipads
            is_iphone = self.device_manager.get_current_device_model().startswith("iPhone")
            if not is_iphone:
                # force looping
                tweaks[TweakID.PosterBoard].loop_video = True
            is_looping = tweaks[TweakID.PosterBoard].loop_video
            self.ui.pbVideoThumbLbl.setVisible(is_iphone and not is_looping)
            self.ui.chooseThumbBtn.setVisible(is_iphone and not is_looping)
            self.ui.caVideoChk.setVisible(is_iphone)
            self.ui.exportPBVideoBtn.setVisible(is_looping and tweaks[TweakID.PosterBoard].videoFile != None)
            # show status bar date on ipads
            self.ui.dateChk.setVisible(not is_iphone)
            self.ui.dateTxt.setVisible(not is_iphone)
            # show floating tab bar on ipads
            self.ui.floatingTabBarContent.setVisible(not is_iphone)
            # iPadOS stuff
            self.ui.stageManagerChk.setVisible(not is_iphone)
            # liquid glass low performance mode stuff
            supports_lg = device_ver >= Version("26.0")
            # show the disable toggle on iPhone 12s and below (iPhone13,*)
            is_lglpm = self.device_manager.get_current_device_model().removeprefix("iPhone") < "14"
            self.ui.enableLGLPMChk.setVisible(supports_lg and not is_lglpm)
            self.ui.disableLGLPMChk.setVisible(supports_lg and is_lglpm)

            # jjtech/duy books vs sparse restore
            has_sparserestore = self.device_manager.data_singleton.current_device.has_partial_sparserestore()
            self.ui.duyBtn.setVisible(not has_sparserestore)
            self.ui.jjtechBtn.setVisible(has_sparserestore)
            keys_lang_code = self.device_manager.data_singleton.current_device.locale
            if keys_lang_code == 'en_US':
                keys_lang_code = 'en'
            tweaks[TweakID.Passcode].language_code = keys_lang_code
            self.ui.passthmLanguageCodeTxt.setText(keys_lang_code)

            # swap out the current posterboard file
            if tweaks[TweakID.PosterBoard].config_manager.update_for_saved_database(self.device_manager.get_current_device_udid()):
                self.ui.pbDBLbl.setText("sqlite: Selected")
            else:
                self.ui.pbDBLbl.setText("sqlite: None")
            self.update_pb_saved_ids_list()
            # wallpapers are always applied as configurations (iOS 26+ data
            # store layout); the descriptors method is gone, so hide the toggle
            self.ui.pbApplyMethods.setVisible(False)
            tweaks[TweakID.PosterBoard].use_configs = True

            # show the PB if initial load is true
            if self.initial_load:
                self.initial_load = False
                if len(tweaks[TweakID.PosterBoard].tendies) > 0:
                    self.pages[Page.Posterboard].load()
                    self.ui.pages.setCurrentIndex(Page.Posterboard.value)
                    self.ui.posterboardPageBtn.setChecked(True)
                    self.ui.homePageBtn.setChecked(False)
                elif len(tweaks[TweakID.Templates].templates) > 0:
                    self.pages[Page.Templates].load()
                    self.ui.pages.setCurrentIndex(Page.Templates.value)
                    self.ui.templatePageBtn.setChecked(True)
                    self.ui.homePageBtn.setChecked(False)
        else:
            self.device_manager.set_current_device(index=None)

        # update the interface
        self.updateInterfaceForNewDevice()
        self.ios_home.update_device_info()
        self.ios_home.update_status()
        if index > -1:
            self.warn_for_dev_beta()

    def loadSettings(self):
        try:
            # load the settings
            auto_reboot = self.settings.value("auto_reboot", True, type=bool)
            ignore_frame_limit = self.settings.value("ignore_pb_frame_limit", False, type=bool)
            disable_tendies_limit = self.settings.value("disable_tendies_limit", False, type=bool)
            auto_refresh_posterboard = self.settings.value("auto_refresh_posterboard", True, type=bool)

            skip_setup = self.settings.value("skip_setup", True, type=bool)
            supervised = self.settings.value("supervised", False, type=bool)
            organization_name = self.settings.value("organization_name", "", type=str)
            use_encrypted_backup = self.settings.value("use_encrypted_backup", False, type=bool)

            self.ui.autoRebootChk.setChecked(auto_reboot)
            self.ui.ignorePBFrameLimitChk.setChecked(ignore_frame_limit)
            self.ui.disableTendiesLimitChk.setChecked(disable_tendies_limit)
            self.ui.forcePBRefreshChk.setChecked(auto_refresh_posterboard)
            # Experimental encrypted backup option
            if hasattr(self.ui, 'encryptedBackupChk'):
                self.ui.encryptedBackupChk.setChecked(use_encrypted_backup)
            
            self.ui.skipSetupChk.setChecked(skip_setup)
            self.ui.supervisionChk.setChecked(supervised)
            self.ui.supervisionOrganization.setText(organization_name)

            # hide/show the warning label
            if skip_setup:
                self.ui.skipSetupOnLbl.show()
            else:
                self.ui.skipSetupOnLbl.hide()

            self.device_manager.pref_manager.auto_reboot = auto_reboot
            video_handler.set_ignore_frame_limit(ignore_frame_limit)
            self.device_manager.pref_manager.disable_tendies_limit = disable_tendies_limit
            self.device_manager.pref_manager.auto_refresh_posterboard = auto_refresh_posterboard
            self.device_manager.pref_manager.use_encrypted_backup = use_encrypted_backup
            self.device_manager.pref_manager.skip_setup = skip_setup
            self.device_manager.pref_manager.supervised = supervised
            self.device_manager.pref_manager.organization_name = organization_name
        except Exception:
            pass
    
    def _load_last_preset(self):
        """Load the latest autosaved preset on startup.

        Prefers the AutoSave preset (written on every tweak change) so the UI
        restores the most recent configuration. Falls back to the last
        manually-loaded preset when no autosave exists.
        """
        if "AutoSave" in self.preset_manager.list_presets():
            self.preset_manager.load_preset("AutoSave")
            return
        last_preset = self.settings.value("last_loaded_preset", "", type=str)
        if last_preset:
            self.preset_manager.load_preset(last_preset)

    def _register_tweak_autosave(self):
        """Register callback to auto-save preset when tweaks change."""
        set_tweak_change_callback(self._on_tweak_changed)

    def _on_tweak_changed(self):
        """Called when any tweak value changes - schedule autosave."""
        if self._preset_autosave_pending:
            return
        self._preset_autosave_pending = True
        # Debounce: save after 500ms of no changes
        QtCore.QTimer.singleShot(500, self._save_autosave_preset)

    def _save_autosave_preset(self):
        """Save current tweak state to AutoSave preset."""
        self._preset_autosave_pending = False
        try:
            self.preset_manager.save_preset(
                "AutoSave", "Automatic save of last tweak configuration", tags=["auto"],
                device_model=self.device_manager.get_current_device_model() or "",
                ios_version=self.device_manager.get_current_device_version() or "")
        except Exception:
            pass  # Silent fail - autosave is best-effort
     
    
    ## SIDE BAR FUNCTIONS
    def is_ios_theme(self) -> bool:
        return self.theme_manager.current_theme == ThemeManager.IOS

    def eventFilter(self, obj, event):
        """Handle ESC and the mouse back button as navigation-back.

        Installed app-wide so it works regardless of which widget has focus.
        Modal dialogs (QInputDialog, QMessageBox, file pickers, ...) are left
        untouched so ESC keeps closing them.
        """
        if QtWidgets.QApplication.activeModalWidget() is not None:
            return super().eventFilter(obj, event)
        etype = event.type()
        if etype == QtCore.QEvent.Type.KeyPress and event.key() == QtCore.Qt.Key.Key_Escape:
            return self._go_back()
        if etype == QtCore.QEvent.Type.MouseButtonPress and event.button() in (
                QtCore.Qt.MouseButton.BackButton, QtCore.Qt.MouseButton.ExtraButton1):
            return self._go_back()
        return super().eventFilter(obj, event)

    def _go_back(self) -> bool:
        """Navigate back to the iOS home page. Returns True if the event was consumed.

        Only applies to the new iOS UI; the classic UI keeps its own sidebar
        navigation and does not react to ESC / mouse back button.
        """
        if not self.is_ios_theme():
            return False
        if self.ios_pages.currentIndex() != 0:
            self.ios_pages.setCurrentIndex(0)
            return True
        return False

    def on_homePageBtn_clicked(self):
        self.ui.pages.setCurrentIndex(Page.Home.value)
    
    def on_statusBarPageBtn_clicked(self):
        self.pages[Page.StatusBar].load()
        self.ui.sbScrollArea.verticalScrollBar().setValue(0) # reset scroll to top
        self.ui.pages.setCurrentIndex(Page.StatusBar.value)

    def on_springboardOptionsPageBtn_clicked(self):
        self.pages[Page.Springboard].load()
        self.ui.pages.setCurrentIndex(Page.Springboard.value)

    def on_internalOptionsPageBtn_clicked(self):
        self.pages[Page.InternalOptions].load()
        self.ui.pages.setCurrentIndex(Page.InternalOptions.value)

    def on_liquidGlassPageBtn_clicked(self):
        self.pages[Page.LiquidGlass].load()
        self.ui.pages.setCurrentIndex(Page.LiquidGlass.value)

    def on_daemonsPageBtn_clicked(self):
        self.pages[Page.Daemons].load()
        self.ui.pages.setCurrentIndex(Page.Daemons.value)

    def on_posterboardPageBtn_clicked(self):
        self.pages[Page.Posterboard].load()
        self.ui.pages.setCurrentIndex(Page.Posterboard.value)

    def on_templatesPageBtn_clicked(self):
        self.pages[Page.Templates].load()
        self.ui.pages.setCurrentIndex(Page.Templates.value)

    def on_tweaksPageBtn_clicked(self):
        self.ui.pages.setCurrentIndex(Page.Tweaks.value)

    def on_applyPageBtn_clicked(self):
        self.ui.pages.setCurrentIndex(Page.Apply.value)

    def on_settingsPageBtn_clicked(self):
        self.pages[Page.Settings].load()
        self.ui.pages.setCurrentIndex(Page.Settings.value)

    ## APPLY PAGE

    def show_about_dialog(self):
        dialog = AboutProgramDialog(self)
        dialog.exec()

    def update_label(self, txt: str):
        self.ui.statusLbl.setText(txt)
        # Mirror progress into the iOS home indicator when in iOS theme
        try:
            if self.is_ios_theme() and txt:
                self.ios_home.show_process_status(txt)
        except Exception:
            pass
    def on_removeTweaksBtn_clicked(self):
        dialog = ResetDialog(device_manager=self.device_manager, apply_reset=self.apply_changes)
        dialog.exec()

    @QtCore.Slot()
    def on_applyTweaksBtn_clicked(self):
        self.apply_changes()

    def apply_changes(self, reset_pages: list=None):
        if not self.apply_in_progress:
            self.apply_in_progress = True
            self.toggle_thread_btns(disabled=True)
            self.worker_thread = ApplyThread(manager=self.device_manager, settings=self.settings, reset_pages=reset_pages)
            self.worker_thread.progress.connect(self.update_label)
            self.worker_thread.alert.connect(self.alert_message)
            self.worker_thread.finished_with_result.connect(self.finish_apply_thread)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.start()
    def alert_message(self, alert: Optional[ApplyAlertMessage], log_to_console: bool = True):
        if alert is None:
            # do sudo dialog input
            get_sudo_pwd() # clear if it is already there
            pwd, ok = QtWidgets.QInputDialog.getText(None, "Enter Sudo Password", "Enter Your Computer's Password:", QtWidgets.QLineEdit.Password, "")
            if ok and pwd:
                set_sudo_pwd(pwd)
            return
        if log_to_console:
            print(alert.txt)
        detailsBox = QtWidgets.QMessageBox()
        detailsBox.setIcon(alert.icon)
        detailsBox.setWindowTitle(alert.title)
        detailsBox.setText(alert.txt)
        if alert.detailed_txt != None:
            detailsBox.setDetailedText(alert.detailed_txt)
        detailsBox.exec()

    def finish_apply_thread(self, success: bool = False, error_msg: str = ""):
        self.apply_in_progress = False
        self.toggle_thread_btns(disabled=False)
        self.update_pb_saved_ids_list()
        worker = getattr(self, 'worker_thread', None)
        is_reset = worker is not None and worker.reset_pages is not None
        # Show completion indicator on the iOS home page
        try:
            if self.is_ios_theme():
                if success:
                    self.ios_home.show_process_status(
                        QCoreApplication.tr("Reset complete!") if is_reset else QCoreApplication.tr("Apply complete!"),
                        success=True)
                else:
                    self.ios_home.show_process_status(
                        QCoreApplication.tr("Operation failed"), success=False)
        except Exception:
            pass
        if success:
            if worker is not None and not is_reset:
                self.prompt_star_on_github()
        else:
            # Show error notification if not already shown via alert
            if error_msg and "timed out" not in error_msg.lower():
                self.alert_message(ApplyAlertMessage(
                    txt=f"Operation failed: {error_msg}",
                    title="Error",
                    icon=QtWidgets.QMessageBox.Critical
                ), log_to_console=False)
    def prompt_star_on_github(self):
        if self.settings.value("star_prompt_done", False, type=bool):
            return
        self.settings.setValue("star_prompt_done", True)
        self._sync_settings()
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Question)
        box.setWindowTitle(self.tr("Enjoying GoldenNugget?"))
        box.setText(self.tr("If you like GoldenNugget, please consider giving it a star on GitHub!"))
        star_btn = box.addButton(self.tr("Star on GitHub"), QtWidgets.QMessageBox.AcceptRole)
        box.addButton(self.tr("Not now"), QtWidgets.QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() == star_btn:
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QtCore.QUrl("https://github.com/awesomenull-dev/GoldenNugget"))

    def _sync_settings(self):
        """Sync settings to disk immediately after critical changes."""
        try:
            self.settings.sync()
        except Exception:
            pass  # Best effort
    def toggle_thread_btns(self, disabled: bool):
        if disabled or not self.apply_in_progress:
            self.ui.applyTweaksBtn.setDisabled(disabled)
            self.ui.removeTweaksBtn.setDisabled(disabled)
        if disabled or not self.refresh_in_progress:
            self.ui.refreshBtn.setDisabled(disabled)
