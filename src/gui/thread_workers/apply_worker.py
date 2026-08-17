from PySide6.QtCore import Signal, QThread, QSettings, QTimer
from PySide6.QtWidgets import QMessageBox
from typing import Optional
import traceback
import threading

from src.gui.pages.pages_list import Page


class ApplyAlertMessage:
    def __init__(self, txt: str, title: str = "Error!", icon=QMessageBox.Critical, detailed_txt: str = None, is_revert: bool = False, backup_path: str = None):
        self.txt = txt
        self.title = title
        self.icon = icon
        self.detailed_txt = detailed_txt
        self.is_revert = is_revert
        self.backup_path = backup_path


class _SudoState:
    """Thread-safe sudo password storage."""
    def __init__(self):
        self._lock = threading.Lock()
        self._pwd: Optional[str] = None
        self._complete = False

    def get_pwd(self) -> Optional[str]:
        with self._lock:
            pwd = self._pwd
            self._pwd = None
            self._complete = False
            return pwd

    def get_complete(self) -> bool:
        with self._lock:
            return self._complete

    def set_complete(self, complete: bool):
        with self._lock:
            self._complete = complete

    def set_pwd(self, pwd: Optional[str]):
        with self._lock:
            self._pwd = pwd


_sudo_state = _SudoState()


def get_sudo_pwd() -> Optional[str]:
    return _sudo_state.get_pwd()


def get_sudo_complete() -> bool:
    return _sudo_state.get_complete()


def set_sudo_complete(is_complete: bool):
    _sudo_state.set_complete(is_complete)


def set_sudo_pwd(pwd: Optional[str]):
    _sudo_state.set_pwd(pwd)


class ApplyAlertMessage:
    def __init__(self, txt: str, title: str = "Error!", icon=QMessageBox.Critical, detailed_txt: str = None, is_revert: bool = False, backup_path: str = None):
        self.txt = txt
        self.title = title
        self.icon = icon
        self.detailed_txt = detailed_txt
        self.is_revert = is_revert
        self.backup_path = backup_path


class ApplyThread(QThread):
    progress = Signal(str)
    alert = Signal(object)  # ApplyAlertMessage or None for sudo prompt
    finished_with_result = Signal(bool, str)  # success, error_message

    _TIMEOUT_MS = 10 * 60 * 1000  # 10 minutes max for apply/restore

    def __init__(self, manager, settings: QSettings, reset_pages: Optional[list[Page]] = None, capture_only: bool = False, revert_last_apply_only: bool = False):
        super().__init__()
        self.manager = manager
        self.settings = settings
        self.reset_pages = reset_pages
        self.capture_only = capture_only
        self.revert_last_apply_only = revert_last_apply_only
        self.success = False
        self._error_msg: str = ""
        self._timeout_timer: Optional[QTimer] = None

    def update_label(self, txt: str):
        if txt == 'sudo_pwd':
            self.alert.emit(None)
        else:
            self.progress.emit(txt)

    def alert_window(self, msg: ApplyAlertMessage):
        self.alert.emit(msg)

    def _on_timeout(self):
        self._error_msg = "Operation timed out after 10 minutes"
        self.alert.emit(ApplyAlertMessage(
            self._error_msg,
            title="Timeout",
            icon=QMessageBox.Critical,
            detailed_txt="The operation took too long and was cancelled. Check device connection and try again."
        ))
        self.terminate()

    def run(self):
        self._timeout_timer = QTimer()
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)
        self._timeout_timer.start(self._TIMEOUT_MS)

        try:
            self._do_work()
            self.success = True
            self._error_msg = ""
            self.finished_with_result.emit(True, "")
        except Exception as e:
            self.success = False
            self._error_msg = f"{type(e).__name__}: {e}"
            traceback_str = traceback.format_exc()
            self.alert.emit(ApplyAlertMessage(
                f"Operation failed: {e}",
                title="Error",
                icon=QMessageBox.Critical,
                detailed_txt=traceback_str
            ))
            self.finished_with_result.emit(False, self._error_msg)
        finally:
            if self._timeout_timer:
                self._timeout_timer.stop()

    def _do_work(self):
        if self.revert_last_apply_only:
            self.manager.revert_last_apply(self.update_label, self.alert_window)
        elif self.capture_only:
            self.manager.capture_originals(self.update_label, self.alert_window)
        elif self.reset_pages is None:
            self.manager.apply_changes(self.update_label, self.alert_window)
        else:
            self.manager.reset_tweaks(self.reset_pages, self.settings, self.update_label, self.alert_window)


class RefreshDevicesThread(QThread):
    alert = Signal(object)

    def __init__(self, manager, settings):
        super().__init__()
        self.manager = manager
        self.settings = settings

    def alert_window(self, msg: ApplyAlertMessage):
        self.alert.emit(msg)

    def run(self):
        try:
            self.manager.get_devices(self.settings, self.alert_window)
        except Exception as e:
            self.alert.emit(ApplyAlertMessage(
                f"Failed to refresh devices: {e}",
                title="Error",
                icon=QMessageBox.Critical,
                detailed_txt=traceback.format_exc()
            ))


def get_sudo_pwd() -> Optional[str]:
    return _sudo_state.get_pwd()


def get_sudo_complete() -> bool:
    return _sudo_state.get_complete()


def set_sudo_complete(is_complete: bool):
    _sudo_state.set_complete(is_complete)


def set_sudo_pwd(pwd: Optional[str]):
    _sudo_state.set_pwd(pwd)