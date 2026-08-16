from PySide6.QtCore import Qt, QCoreApplication, Signal as pyqtSignal
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QDialog,
    QDialogButtonBox, QLineEdit, QSpinBox, QFormLayout, QScrollArea
)


class IOSSectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("iosSectionHeader")
        self.setProperty("cls", "iosSectionHeader")
        self.setStyleSheet("font-size: 13px; font-weight: 600; color: #8E8E93; text-transform: uppercase; letter-spacing: 0.5px; padding-left: 4px;")


class IOSCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("iosCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            IOSCard {
                background-color: #1C1C1E;
                border-radius: 12px;
                border: none;
            }
        """)
        # Don't create a default layout - let the caller decide


class IOSNavBar(QWidget):
    def __init__(self, title: str, on_back=None, right_action=None, window=None, parent=None):
        super().__init__(parent)
        self.setObjectName("iosNavBar")
        self.setFixedHeight(56)
        self.setStyleSheet("background-color: #1C1C1E; border-bottom: 1px solid #3A3A3C;")
        self.window = window
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        # Show back button if on_back callback is provided OR window is provided (to go back to iOS home)
        if on_back or window:
            back_btn = QPushButton(QCoreApplication.translate("IOSNavBar", "←  Back"), self)
            back_btn.setCursor(Qt.PointingHandCursor)
            back_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #007AFF;
                    font-size: 17px;
                    font-weight: 400;
                    border: none;
                    padding: 8px 0;
                }
                QPushButton:hover { color: #0066CC; }
            """)
            back_btn.clicked.connect(self._handle_back)
            layout.addWidget(back_btn)
        else:
            layout.addSpacing(60)

        title_lbl = QLabel(title, self)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(title_lbl, 1)

        if right_action:
            label_text, callback = right_action
            btn = QPushButton(label_text, self)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #007AFF;
                    font-size: 17px;
                    font-weight: 400;
                    border: none;
                    padding: 8px 0;
                }
                QPushButton:hover { color: #0066CC; }
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        else:
            layout.addSpacing(60)

    def _handle_back(self):
        if self.window and hasattr(self.window, 'ios_pages'):
            self.window.ios_pages.setCurrentIndex(0)


class IOSSettingsRow(QPushButton):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName("iosSettingsRow")
        self.setCursor(Qt.PointingHandCursor)
        self.setText(f"{title}  ›")
        self.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1E;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                text-align: left;
                padding: 14px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #2C2C2E; }
        """)


class IOSPrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("iosPrimaryButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border-radius: 12px;
                color: #FFFFFF;
                font-size: 17px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #0066CC; }
            QPushButton:pressed { background-color: #0055AA; }
            QPushButton:disabled { background-color: #3A3A3C; color: #8E8E93; }
        """)


class IOSSwitch(QPushButton):
    """iOS-style toggle switch"""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(51, 31)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.toggled.connect(self._update_style)

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background-color: #30D158;
                    border-radius: 15px;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3A3A3C;
                    border-radius: 15px;
                    border: none;
                }
            """)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.toggled.emit(self.isChecked())


class IOSValueLabel(QLabel):
    """Label showing current value in parentheses"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: #8E8E93; font-size: 14px;")
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
