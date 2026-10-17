from PySide6.QtWidgets import QMessageBox
from typing import Optional


class ApplyAlertMessage:
    def __init__(self, txt: str, title: str = "Error!", icon=QMessageBox.Critical, detailed_txt: str = None, backup_path: str = None):
        self.txt = txt
        self.title = title
        self.icon = icon
        self.detailed_txt = detailed_txt
        self.backup_path = backup_path