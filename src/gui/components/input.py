"""
iOS-style Input components.
"""

from PySide6.QtWidgets import QLineEdit, QComboBox, QTextEdit
from PySide6.QtCore import Qt

from ..theme import iOSColors, iOSRadius, is_theme_enabled


class iOSLineEdit(QLineEdit):
    """iOS-style line edit with proper styling."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(placeholder)
        if not is_theme_enabled():
            return
            
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {iOSColors.CARD_BORDER};
                background-color: {iOSColors.BG_SECONDARY};
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                padding: 12px 16px;
                border-radius: 10px;
                selection-background-color: #007AFF;
            }}
            QLineEdit:focus {{
                border: 2px solid #007AFF;
            }}
            QLineEdit:disabled {{
                background-color: #2C2C2E;
                color: #EBEBF52E;
                border-color: #3A3A3C;
            }}
        """)


class iOSPasswordLineEdit(QLineEdit):
    """iOS-style password field with show/hide toggle."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(placeholder)
        if not is_theme_enabled():
            return
            
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {iOSColors.CARD_BORDER};
                background-color: {iOSColors.BG_SECONDARY};
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                padding: 12px 16px;
                border-radius: 10px;
                selection-background-color: #007AFF;
            }}
            QLineEdit:focus {{
                border: 2px solid #007AFF;
            }}
            QLineEdit:disabled {{
                background-color: #2C2C2E;
                color: #EBEBF52E;
                border-color: #3A3A3C;
            }}
        """)


class iOSComboBox(QComboBox):
    """iOS-style combo box."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {iOSColors.CARD_BORDER};
                background-color: {iOSColors.BG_SECONDARY};
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                padding: 12px 16px;
                border-radius: 10px;
                min-height: 44px;
            }}
            QComboBox:hover {{
                border-color: {iOSColors.TEXT_TERTIARY};
            }}
            QComboBox:focus {{
                border: 2px solid #007AFF;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 32px;
            }}
            QComboBox::down-arrow {{
                image: url(:/icon/chevron.down.svg);
                width: 16px;
                height: 16px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {iOSColors.BG_SECONDARY};
                border: 1px solid {iOSColors.CARD_BORDER};
                border-radius: 10px;
                selection-background-color: #007AFF;
                selection-color: white;
                outline: none;
                padding: 8px;
            }}
        """)


class iOSTextEdit(QTextEdit):
    """iOS-style multi-line text edit."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {iOSColors.CARD_BORDER};
                background-color: {iOSColors.BG_SECONDARY};
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                padding: 12px 16px;
                border-radius: 10px;
                selection-background-color: #007AFF;
            }}
            QTextEdit:focus {{
                border: 2px solid #007AFF;
            }}
        """)