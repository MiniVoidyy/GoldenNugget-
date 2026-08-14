"""
iOS-style Card component.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from ..theme import iOSColors, iOSSpacing, iOSRadius, is_theme_enabled


class iOSCard(QFrame):
    """iOS-style card container with subtle border and rounded corners."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.setObjectName("iOSCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            #iOSCard {{
                background-color: {iOSColors.CARD_BG};
                border: 1px solid {iOSColors.CARD_BORDER};
                border-radius: {iOSRadius.RADIUS_MD}px;
            }}
        """)
        self.setContentsMargins(
            iOSSpacing.SPACING_4, iOSSpacing.SPACING_4,
            iOSSpacing.SPACING_4, iOSSpacing.SPACING_4
        )
        
        # Default layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            iOSSpacing.SPACING_4, iOSSpacing.SPACING_4,
            iOSSpacing.SPACING_4, iOSSpacing.SPACING_4
        )
        self._layout.setSpacing(iOSSpacing.SPACING_3)


class iOSCardSection(QWidget):
    """A section within a card - groups related controls with a header."""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(iOSSpacing.SPACING_2)
        
        if title:
            from .label import iOSLabel
            self.header = iOSLabel(title, style="section")
            self._layout.addWidget(self.header)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(iOSSpacing.SPACING_2)
        self._layout.addWidget(self.content)
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.content_layout.addLayout(layout)