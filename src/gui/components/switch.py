"""
iOS-style Switch component (styled QCheckBox).
"""

from PySide6.QtWidgets import QCheckBox, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

from ..theme import iOSColors, iOSSpacing, is_theme_enabled


class iOSSwitch(QCheckBox):
    """iOS-style toggle switch."""
    
    toggled = Signal(bool)
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        if not is_theme_enabled():
            return
            
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(self.toggled.emit)
        
        if is_theme_enabled():
            self.setStyleSheet(f"""
                QCheckBox {{
                    spacing: {8}px;
                    font-size: 17px;
                    color: {iOSColors.TEXT_PRIMARY};
                }}
                QCheckBox::indicator {{
                    width: 51px;
                    height: 31px;
                    border-radius: 15.5px;
                    border: 2px solid {iOSColors.CARD_BORDER};
                    background-color: {iOSColors.BG_QUATERNARY};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {iOSColors.ACCENT_GREEN};
                    border: 2px solid {iOSColors.ACCENT_GREEN};
                }}
                QCheckBox::indicator:checked:hover {{
                    background-color: {iOSColors.ACCENT_GREEN_HOVER};
                }}
                QCheckBox::indicator:disabled {{
                    background-color: {iOSColors.BG_QUATERNARY};
                    border-color: {iOSColors.SEPARATOR};
                }}
                QCheckBox:disabled {{
                    color: {iOSColors.TEXT_QUATERNARY};
                }}
            """)


class iOSSwitchRow(QWidget):
    """A row with label and switch on the right (iOS Settings style)."""
    
    toggled = Signal(bool)
    
    def __init__(self, title="", subtitle="", checked=False, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Left side - labels
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {iOSColors.TEXT_PRIMARY};
            font-size: 17px;
            font-weight: 400;
        """)
        left_layout.addWidget(self.title_label)
        
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setStyleSheet(f"""
                color: {iOSColors.TEXT_TERTIARY};
                font-size: 13px;
            """)
            left_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - switch
        self.switch = iOSSwitch()
        self.switch.setChecked(checked)
        self.switch.toggled.connect(self.toggled.emit)
        layout.addWidget(self.switch)
    
    def isChecked(self):
        return self.switch.isChecked()
    
    def setChecked(self, checked):
        self.switch.setChecked(checked)