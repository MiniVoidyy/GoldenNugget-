"""
iOS-style Progress Bar component.
"""

from PySide6.QtWidgets import QProgressBar, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from ..theme import iOSColors, iOSRadius, is_theme_enabled


class iOSProgressBar(QProgressBar):
    """iOS-style progress bar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {iOSColors.BG_QUATERNARY};
                border-radius: {iOSRadius.RADIUS_SM}px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: #007AFF;
                border-radius: {iOSRadius.RADIUS_SM}px;
            }}
        """)


class iOSProgressBarWithLabel(QWidget):
    """Progress bar with label above."""
    
    def __init__(self, label="", parent=None):
        super().__init__()
        
        from PySide6.QtWidgets import QVBoxLayout
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        if label:
            from .label import iOSLabel
            self.label = iOSLabel(label, style="caption")
            layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
    
    def setValue(self, value):
        self.progress.setValue(value)
    
    def setMaximum(self, maximum):
        self.progress.setMaximum(maximum)
    
    def setFormat(self, format):
        self.progress.setFormat(format)