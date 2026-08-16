from PySide6.QtCore import Signal, QThread, QSettings
from PySide6.QtWidgets import QMessageBox
from typing import Optional

from src.gui.pages.pages_list import Page

# Global Vars
sudo_pwd = None # reset this variable whenever it is used
sudo_action_complete = False
def get_sudo_pwd() -> Optional[str]:
    pre_reset = sudo_pwd
    set_sudo_pwd(None)
    set_sudo_complete(False)
    return pre_reset
def get_sudo_complete() -> bool:
    return sudo_action_complete
def set_sudo_complete(isComplete: bool):
    global sudo_action_complete
    sudo_action_complete = isComplete
def set_sudo_pwd(pwd: Optional[str]):
    global sudo_pwd
    sudo_pwd = pwd

class ApplyAlertMessage:
    def __init__(self, txt: str, title: str = "Error!", icon = QMessageBox.Critical, detailed_txt: str = None, is_revert: bool = False, backup_path: str = None):
        self.txt = txt
        self.title = title
        self.icon = icon
        self.detailed_txt = detailed_txt
        self.is_revert = is_revert
        self.backup_path = backup_path

class ApplyThread(QThread):
    progress = Signal(str)
    alert = Signal(ApplyAlertMessage)

    def update_label(self, txt: str):
        if txt == 'sudo_pwd':
            # hacky workaround
            self.alert.emit(None)
        else:
            self.progress.emit(txt)
    def alert_window(self, msg: ApplyAlertMessage):
        self.alert.emit(msg)
    
    def __init__(self, manager, settings: QSettings, reset_pages: Optional[list[Page]] = None, capture_only: bool = False, revert_last_apply_only: bool = False):
        super().__init__()
        self.manager = manager
        self.settings = settings
        self.reset_pages = reset_pages
        self.capture_only = capture_only
        self.revert_last_apply_only = revert_last_apply_only
        self.success = False

    def do_work(self):
        if self.revert_last_apply_only:
            # reverting the last apply (auto-revert)
            self.manager.revert_last_apply(self.update_label, self.alert_window)
        elif self.capture_only:
            # saving the original plists
            self.manager.capture_originals(self.update_label, self.alert_window)
        elif self.reset_pages == None:
            # applying tweaks
            self.manager.apply_changes(self.update_label, self.alert_window)
        else:
            # resetting tweaks
            self.manager.reset_tweaks(self.reset_pages, self.settings, self.update_label, self.alert_window)

    def run(self):
        try:
            self.do_work()
            self.success = True
        except Exception as e:
            self.success = False
            print(f"ApplyThread error: {e}")

class RefreshDevicesThread(QThread):
    alert = Signal(ApplyAlertMessage)

    def alert_window(self, msg: ApplyAlertMessage):
        self.alert.emit(msg)

    def __init__(self, manager, settings):
        super().__init__()
        self.manager = manager
        self.settings = settings

    def do_work(self):
        self.manager.get_devices(self.settings, self.alert_window)

    def run(self):
        self.do_work()