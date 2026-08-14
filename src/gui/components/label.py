"""
iOS-style Label components.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from ..theme import iOSColors, is_theme_enabled


class iOSLabel(QLabel):
    """iOS-style label with predefined styles."""
    
    STYLE_BODY = "body"
    STYLE_CALLOUT = "callout"
    STYLE_SUBHEADLINE = "subheadline"
    STYLE_FOOTNOTE = "footnote"
    STYLE_CAPTION_1 = "caption1"
    STYLE_CAPTION_2 = "caption2"
    STYLE_SECTION = "section"
    STYLE_TITLE = "title"
    STYLE_HEADLINE = "headline"
    
    def __init__(self, text="", style=STYLE_BODY, parent=None):
        super().__init__(text, parent)
        if not is_theme_enabled():
            return
            
        self.style_type = style
        self.setWordWrap(True)
        self._apply_style()
    
    def _apply_style(self):
        if not is_theme_enabled():
            return
            
        styles = {
            self.STYLE_BODY: f"""
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                font-weight: 400;
            """,
            self.STYLE_CALLOUT: f"""
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 400;
            """,
            self.STYLE_SUBHEADLINE: f"""
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 15px;
                font-weight: 400;
            """,
            self.STYLE_FOOTNOTE: f"""
                color: {iOSColors.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 400;
            """,
            self.STYLE_CAPTION_1: f"""
                color: {iOSColors.TEXT_TERTIARY};
                font-size: 12px;
                font-weight: 400;
            """,
            self.STYLE_CAPTION_2: f"""
                color: {iOSColors.TEXT_QUATERNARY};
                font-size: 11px;
                font-weight: 400;
            """,
            self.STYLE_SECTION: f"""
                color: {iOSColors.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 0 4px 0;
            """,
            self.STYLE_TITLE: f"""
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 28px;
                font-weight: 700;
            """,
            self.STYLE_HEADLINE: f"""
                color: {iOSColors.TEXT_PRIMARY};
                font-size: 17px;
                font-weight: 600;
            """,
        }
        
        self.setStyleSheet(styles.get(self.style_type, styles[self.STYLE_BODY]))
    
    def setText(self, text):
        if self.style_type == "section":
            text = text.upper()
        super().setText(text)


class iOSSectionHeader(QLabel):
    """iOS Settings-style section header (uppercase, small, 60% opacity)."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text.upper(), parent)
        if not is_theme_enabled():
            return
            
        self.setStyleSheet(f"""
            color: #EBEBF599;
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
        self.setStyleSheet("""
            color: #EBEBF54D;
            font-size: 13px;
            padding-top: 4px;
        """)