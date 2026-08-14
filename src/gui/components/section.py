"""
iOS-style Section Header component.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from ..theme import iOSColors, iOSSpacing, is_theme_enabled


class iOSSectionHeader(QLabel):
    """iOS Settings-style section header (uppercase, small, 60% opacity)."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text.upper(), parent)
        if not is_theme_enabled():
            return
            
        self.setStyleSheet(f"""
            color: {iOSColors.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 8px 0 4px 0;
        """)
    
    def setText(self, text):
        super().setText(text.upper())


class iOSSectionFooter(QLabel):
    """iOS-style section footer (explanatory text at bottom of section)."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        if not is_theme_enabled():
            return
            
        self.setWordWrap(True)
        self.setStyleSheet(f"""
            color: {iOSColors.TEXT_TERTIARY};
            font-size: 13px;
            padding-top: 4px;
        """)