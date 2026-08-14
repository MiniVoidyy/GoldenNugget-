"""
iOS-style Tweaks page component with categories and descriptions.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QWidget, QLabel, QCheckBox, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..theme import iOSColors, iOSSpacing, iOSRadius, is_theme_enabled, is_theme_enabled


class iOSTweakRow(QWidget):
    """A single tweak row with title, description, and toggle."""
    
    toggled = Signal(bool)
    
    def __init__(self, title="", description="", checked=False, tweak_id=None, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.tweak_id = tweak_id
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Left side - title and description
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
        
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet(f"""
                color: {iOSColors.TEXT_TERTIARY};
                font-size: 13px;
            """)
            left_layout.addWidget(self.desc_label)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - iOS-style switch
        self.switch = QCheckBox()
        self.switch.setChecked(checked)
        self.switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch.toggled.connect(self.toggled.emit)
        
        if is_theme_enabled():
            self.switch.setStyleSheet(f"""
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
        
        layout.addWidget(self.switch)
    
    def isChecked(self):
        return self.switch.isChecked()
    
    def setChecked(self, checked):
        self.switch.setChecked(checked)


class iOSTweakSection(QWidget):
    """A section of tweaks with a header."""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        if title:
            header = QLabel(title.upper())
            header.setStyleSheet(f"""
                color: {iOSColors.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 16px 16px 8px 16px;
            """)
            self._layout.addWidget(header)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self._layout.addWidget(self.content)
    
    def add_tweak(self, tweak_row: 'iOSTweakRow'):
        self.content_layout.addWidget(tweak_row)
        
        # Add separator line (except for last item, but we'll add after each)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {iOSColors.SEPARATOR}; max-height: 1px; min-height: 1px; margin-left: 67px;")
        self.content_layout.addWidget(separator)


class iOSTweaksPage(QScrollArea):
    """iOS-style tweaks page with categorized sections."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if not is_theme_enabled():
            return
            
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QWidget { background: transparent; }
            QScrollBar:vertical { width: 6px; background: transparent; }
            QScrollBar::handle { background: #3A3A3C; border-radius: 3px; min-height: 30px; }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        
        self.setWidget(self.content_widget)
        
        # Add default sections - these will be populated by the page
        self.sections = {}
    
    def add_section(self, section_id: str, title: str):
        """Add a new section to the tweaks page."""
        section = iOSTweakSection(title)
        self.sections[section_id] = section
        self.content_layout.addWidget(section)
        return section
    
    def get_section(self, section_id: str):
        return self.sections.get(section_id)
    
    def clear(self):
        for section in self.sections.values():
            section.deleteLater()
        self.sections.clear()
    
    def add_tweak(self, section_id: str, title: str, description: str = "", checked: bool = False, tweak_id=None):
        """Add a tweak to a section."""
        section = self.get_section(section_id)
        if not section:
            return None
        
        tweak = iOSTweakRow(title, description, checked, tweak_id)
        section.add_tweak(tweak)
        return tweak


def create_default_tweaks_page():
    """Create a default tweaks page with all categories populated."""
    from src.tweaks.tweaks import tweaks, TweakID
    
    page = iOSTweaksPage()
    
    # Define categories - only include tweaks that exist in the tweaks dict
    categories = {
        "posterboard": "PosterBoard",
        "templates": "Templates", 
        "statusbar": "Status Bar",
        "passcode": "Passcode Theme",
        "bookrestore": "BookRestore",
    }
    
    for section_id, title in categories.items():
        page.add_section(section_id, title)
    
    # PosterBoard tweaks
    page.add_tweak("posterboard", "PosterBoard", "Manage animated wallpapers and descriptors", 
                   tweaks.get(TweakID.PosterBoard, None) is not None, TweakID.PosterBoard)
    page.add_tweak("posterboard", "Templates", "Custom template operations and file editing",
                   tweaks.get(TweakID.Templates, None) is not None, TweakID.Templates)
    
    # Status Bar tweaks
    page.add_tweak("statusbar", "Status Bar", "Customize status bar items (carrier, battery, time, etc.)",
                   tweaks.get(TweakID.StatusBar, None) is not None, TweakID.StatusBar)
    
    # Passcode Theme
    page.add_tweak("passcode", "Passcode Theme", "Customize passcode screen appearance",
                   tweaks.get(TweakID.Passcode, None) is not None, TweakID.Passcode)
    
    # BookRestore folders
    page.add_tweak("bookrestore", "Create BR Folders", "Create folders for BookRestore feature",
                   tweaks.get(TweakID.CreateBRFolders, None) is not None, TweakID.CreateBRFolders)
    
    return page