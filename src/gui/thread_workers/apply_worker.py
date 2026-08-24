from PySide6.QtCore import Signal, QThread, QSettings
from PySide6.QtWidgets import QMessageBox
from typing import Optional
import queue
import traceback
import threading

from src.gui.pages.pages_list import Page


class ApplyAlertMessage:
    def __init__(self, txt: str, title: str = "Error!", icon=QMessageBox.Critical, detailed_txt: str = None, backup_path: str = None):
        self.txt = txt
        self.title = title
        self.icon = icon
        self.detailed_txt = detailed_txt
        self.backup_path = backup_path


class _SudoState:
    """Thread-safe sudo password storage."""
    def __init__(self):
        self._lock = threading.Lock()
        self._pwd: Optional[str] = None

    def get_pwd(self) -> Optional[str]:
        with self._lock:
            pwd = self._pwd
            self._pwd = None
            return pwd

    def set_pwd(self, pwd: Optional[str]):
        with self._lock:
            self._pwd = pwd


_sudo_state = _SudoState()


def get_sudo_pwd() -> Optional[str]:
    return _sudo_state.get_pwd()


def set_sudo_pwd(pwd: Optional[str]):
    _sudo_state.set_pwd(pwd)


class ApplyThread(QThread):
    progress = Signal(str)
    alert = Signal(object)  # ApplyAlertMessage or None for sudo prompt
    finished_with_result = Signal(bool, str)  # success, error_message
    request_text = Signal(str, str, object)  # title, label, result box (main-thread prompt)

    # Only the password prompt is guarded by a timeout. The apply/restore itself
    # is allowed to run to completion: a three-phase protective restore can
    # legitimately exceed 10 minutes waiting for the device to reboot, and
    # forcibly terminating the worker thread mid-restore (QThread.terminate)
    # would corrupt the device state.
    _PROMPT_TIMEOUT_SEC = 10 * 60

    def __init__(self, manager, settings: QSettings, reset_pages: Optional[list[Page]] = None):
        super().__init__()
        self.manager = manager
        self.settings = settings
        self.reset_pages = reset_pages
        self.success = False
        self._error_msg: str = ""

    def update_label(self, txt: str):
        if txt == 'sudo_pwd':
            self.alert.emit(None)
        else:
            self.progress.emit(txt)

    def alert_window(self, msg: ApplyAlertMessage):
        self.alert.emit(msg)

    def prompt_password(self, title: str, label: str) -> Optional[str]:
        # Modal dialogs must be built on the main thread (macOS raises
        # NSInternalInconsistencyException otherwise), so relay the request
        # through a queued signal while this worker thread blocks on a queue.
        box = queue.Queue(maxsize=1)
        self.request_text.emit(title, label, box)
        try:
            return box.get(timeout=self._PROMPT_TIMEOUT_SEC)
        except queue.Empty:
            return None

    def run(self):
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

    def _do_work(self):
        if self.reset_pages is None:
            self.manager.apply_changes(self.update_label, self.alert_window, self.prompt_password)
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