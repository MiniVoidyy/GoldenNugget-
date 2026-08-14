"""
iOS-style Button components.
"""

from PySide6.QtWidgets import QPushButton, QToolButton, QWidget, QHBoxLayout
from PySide6.QtCore import Qt

from ..theme import iOSColors, iOSSpacing, iOSRadius, is_theme_enabled


class iOSButton(QPushButton):
    """iOS-style button with primary, secondary, and destructive variants."""
    
    STYLE_PRIMARY = "primary"
    STYLE_SECONDARY = "secondary"
    STYLE_DESTRUCTIVE = "destructive"
    STYLE_TERTIARY = "tertiary"  # Plain text button
    
    def __init__(self, text="", style=STYLE_PRIMARY, parent=None):
        super().__init__(text, parent)
        if not is_theme_enabled():
            return
            
        self.style_type = style
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self._apply_style()
    
    def _apply_style(self):
        if not is_theme_enabled():
            return
            
        base_style = f"""
            QPushButton {{
                border: none;
                border-radius: {iOSRadius.RADIUS_MD}px;
                padding: 12px 24px;
                font-size: 17px;
                font-weight: 600;
                min-height: 44px;
            }}
        """
        
        styles = {
            self.STYLE_PRIMARY: f"""
                {base_style}
                QPushButton {{
                    background-color: {iOSColors.ACCENT_BLUE};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {iOSColors.ACCENT_BLUE_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {iOSColors.ACCENT_BLUE_PRESSED};
                }}
                QPushButton:disabled {{
                    background-color: {iOSColors.BG_QUATERNARY} !important;
                    color: {iOSColors.TEXT_QUATERNARY} !important;
                }}
            """,
            self.STYLE_SECONDARY: f"""
                {base_style}
                QPushButton {{
                    background-color: {iOSColors.BG_SECONDARY};
                    color: {iOSColors.ACCENT_BLUE};
                    border: 1px solid {iOSColors.ACCENT_BLUE};
                }}
                QPushButton:hover {{
                    background-color: {iOSColors.BG_TERTIARY};
                }}
                QPushButton:pressed {{
                    background-color: {iOSColors.BG_QUATERNARY};
                }}
                QPushButton:disabled {{
                    background-color: {iOSColors.BG_QUATERNARY} !important;
                    color: {iOSColors.TEXT_QUATERNARY} !important;
                    border-color: {iOSColors.SEPARATOR} !important;
                }}
            """,
            self.STYLE_DESTRUCTIVE: f"""
                {base_style}
                QPushButton {{
                    background-color: {iOSColors.ACCENT_RED};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {iOSColors.ACCENT_RED_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {iOSColors.ACCENT_RED_HOVER};
                }}
                QPushButton:disabled {{
                    background-color: {iOSColors.BG_QUATERNARY} !important;
                    color: {iOSColors.TEXT_QUATERNARY} !important;
                }}
            """,
            self.STYLE_TERTIARY: f"""
                {base_style}
                QPushButton {{
                    background-color: transparent;
                    color: {iOSColors.ACCENT_BLUE};
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {iOSColors.BG_TERTIARY};
                }}
                QPushButton:pressed {{
                    background-color: {iOSColors.BG_QUATERNARY};
                }}
                QPushButton:disabled {{
                    color: {iOSColors.TEXT_QUATERNARY} !important;
                }}
            """,
        }
        
        self.setStyleSheet(styles.get(self.style_type, styles[self.STYLE_PRIMARY]))


class iOSToolButton(QToolButton):
    """iOS-style tool button for toolbar/sidebar use."""
    
    STYLE_PRIMARY = "primary"
    STYLE_SECONDARY = "secondary"
    STYLE_SIDEBAR = "sidebar"
    
    def __init__(self, text="", style=STYLE_PRIMARY, parent=None):
        super().__init__(text)
        if not is_theme_enabled():
            return
            
        self.style_type = style
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()
    
    def _apply_style(self):
        if not is_theme_enabled():
            return
            
        base_style = """
            QToolButton {
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 17px;
                font-weight: 600;
                min-height: 44px;
            }
        """
        
        styles = {
            self.STYLE_PRIMARY: f"""
                {base_style}
                QToolButton {{
                    background-color: {iOSColors.ACCENT_BLUE};
                    color: white;
                }}
                QToolButton:hover {{ background-color: {iOSColors.ACCENT_BLUE_HOVER}; }}
                QToolButton:pressed {{ background-color: {iOSColors.ACCENT_BLUE_PRESSED}; }}
                QToolButton:disabled {{ background-color: {iOSColors.BG_QUATERNARY}; color: {iOSColors.TEXT_QUATERNARY}; }}
            """,
            self.STYLE_SECONDARY: f"""
                {base_style}
                QToolButton {{
                    background-color: {iOSColors.BG_SECONDARY};
                    color: {iOSColors.ACCENT_BLUE};
                    border: 1px solid {iOSColors.ACCENT_BLUE};
                }}
                QToolButton:hover {{ background-color: {iOSColors.BG_TERTIARY}; }}
                QToolButton:pressed {{ background-color: {iOSColors.BG_QUATERNARY}; }}
            """,
            self.STYLE_SIDEBAR: f"""
                QToolButton {{
                    background-color: transparent;
                    color: {iOSColors.TEXT_PRIMARY};
                    font-size: 14px;
                    min-height: 44px;
                    icon-size: 24px;
                    padding: 8px 16px;
                    border-radius: 10px;
                }}
                QToolButton:hover {{ background-color: {iOSColors.BG_TERTIARY}; }}
                QToolButton:checked {{ background-color: {iOSColors.ACCENT_BLUE}; color: white; }}
                QToolButton:disabled {{ color: {iOSColors.TEXT_QUATERNARY}; }}
            """,
        }
        
        self.setStyleSheet(styles.get(self.style_type, styles[self.STYLE_PRIMARY]))


class iOSButtonRow(QWidget):
    """Horizontal row of buttons with proper spacing."""
    
    def __init__(self, buttons=None, spacing=12, parent=None):
        super().__init__(parent)
        
        from PySide6.QtWidgets import QHBoxLayout
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        
        if buttons:
            for btn in buttons:
                layout.addWidget(btn)
        
        layout.addStretch()