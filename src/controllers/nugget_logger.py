import logging
import os
from datetime import datetime

from PySide6.QtCore import QStandardPaths

_active_log_path = None


def get_log_dir() -> str:
    app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    log_dir = os.path.join(app_data_path, "Logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        log_dir = os.path.join(os.path.expanduser("~"), ".nugget_logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            pass
    return log_dir


def get_log_path() -> str:
    if _active_log_path:
        return _active_log_path
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(get_log_dir(), f"nugget_{timestamp}.log")


def init_logging() -> str:
    global _active_log_path
    if _active_log_path is None:
        _active_log_path = get_log_path()
        handler = logging.FileHandler(_active_log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
    return _active_log_path


def log(level: int, message: str):
    logging.getLogger("GoldenNugget").log(level, message)
