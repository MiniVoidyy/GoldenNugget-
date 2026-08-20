import webbrowser

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QFileDialog
)

from src.gui.ios.components import IOSNavBar, IOSSectionHeader, IOSCard, IOSPrimaryButton
from src.tweaks.tweaks import tweaks, TweakID


class IOSPasscodePage(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("iosContainer")
        self.passcode = tweaks[TweakID.Passcode]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = IOSNavBar(QCoreApplication.translate("IOSPasscodePage", "Passcode Themes"), window=self.window)
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

        # Options
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSPasscodePage", "Options")))

        # Key size
        size_card = IOSCard()
        size_row = QHBoxLayout(size_card)
        size_row.setContentsMargins(16, 10, 16, 10)
        size_row.setSpacing(12)
        size_label = QLabel(QCoreApplication.translate("IOSPasscodePage", "Size of Keys"))
        size_label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        size_row.addWidget(size_label, 1)
        self.key_size_drp = QComboBox()
        self.key_size_drp.addItem(QCoreApplication.translate("IOSPasscodePage", "Big"))
        self.key_size_drp.addItem(QCoreApplication.translate("IOSPasscodePage", "Small"))
        self.key_size_drp.setCurrentIndex(0 if self.passcode.big_keys else 1)
        self.key_size_drp.activated.connect(self._on_key_size_selected)
        self.key_size_drp.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1E;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 12px;
                min-width: 120px;
            }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 10px;
                color: #FFFFFF;
                selection-background-color: #007AFF;
            }
        """)
        size_row.addWidget(self.key_size_drp)
        content_layout.addWidget(size_card)

        # Language code
        lang_card = IOSCard()
        lang_row = QHBoxLayout(lang_card)
        lang_row.setContentsMargins(16, 10, 16, 10)
        lang_row.setSpacing(12)
        lang_label = QLabel(QCoreApplication.translate("IOSPasscodePage", "Language Code"))
        lang_label.setStyleSheet("color: #FFFFFF; font-size: 15px;")
        lang_row.addWidget(lang_label, 1)
        self.language_code_txt = QLineEdit()
        self.language_code_txt.setText(self.passcode.language_code)
        self.language_code_txt.setPlaceholderText(QCoreApplication.translate("IOSPasscodePage", "Language Code"))
        self.language_code_txt.textEdited.connect(self._on_language_code_edited)
        self.language_code_txt.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1E;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                padding: 10px 14px;
            }
        """)
        lang_row.addWidget(self.language_code_txt)
        content_layout.addWidget(lang_card)

        # Import
        content_layout.addWidget(IOSSectionHeader(QCoreApplication.translate("IOSPasscodePage", "Theme")))
        import_btn = IOSPrimaryButton(QCoreApplication.translate("IOSPasscodePage", "Import Passcode Theme (.passthm)"))
        import_btn.clicked.connect(self._on_import)
        content_layout.addWidget(import_btn)

        self.selected_lbl = QLabel(QCoreApplication.translate("IOSPasscodePage", "Selected passthm file: None"))
        self.selected_lbl.setStyleSheet("font-size: 13px; color: #8E8E93;")
        self.selected_lbl.setWordWrap(True)
        content_layout.addWidget(self.selected_lbl)

        discover_btn = IOSPrimaryButton(QCoreApplication.translate("IOSPasscodePage", "Discover Themes"))
        discover_btn.clicked.connect(self._on_discover)
        content_layout.addWidget(discover_btn)

        content_layout.addStretch()

    def _on_key_size_selected(self, index: int):
        self.passcode.big_keys = (index == 0)

    def refresh_language_code(self):
        self.language_code_txt.setText(self.passcode.language_code)

    def _on_language_code_edited(self, text: str):
        if len(text) >= 2:
            self.passcode.language_code = text

    def _on_import(self):
        selected_file, _ = QFileDialog.getOpenFileName(
            self.window, QCoreApplication.translate("IOSPasscodePage", "Select Passcode Theme Files"),
            "", "Zip Files (*.passthm)", options=QFileDialog.ReadOnly)
        if selected_file and len(selected_file) > 0:
            self.passcode.import_passthm(path=selected_file)
            self.selected_lbl.setText(QCoreApplication.translate(
                "IOSPasscodePage", "Selected passthm file: {0}").format(selected_file))
        else:
            self.passcode.import_passthm(path=selected_file)
            self.selected_lbl.setText(QCoreApplication.translate("IOSPasscodePage", "Selected passthm file: None"))

    def _on_discover(self):
        webbrowser.open_new_tab("https://cowabun.ga/wallpapers?section=passtheme")