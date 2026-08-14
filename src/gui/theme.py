"""
iOS-style theme system for GoldenNugget.
Enabled via --new-theme command line flag.
"""

import os
import sys
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtCore import QFile, QTextStream

def is_new_theme_enabled():
    """Check if new theme is enabled via command line flag."""
    return "--new-theme" in sys.argv


def set_new_theme_enabled(enabled: bool):
    """Manually set the theme enabled state (for testing)."""
    global _NEW_THEME_ENABLED
    _NEW_THEME_ENABLED = enabled


_NEW_THEME_ENABLED = "--new-theme" in sys.argv


def is_theme_enabled():
    """Check if new theme is currently enabled."""
    return _NEW_THEME_ENABLED


class iOSColors:
    """iOS 17+ dark mode color palette."""
    
    # Background layers
    BG_PRIMARY = "#000000"           # Pure black for OLED
    BG_SECONDARY = "#1C1C1E"         # Elevated surfaces (cards)
    BG_TERTIARY = "#2C2C2E"          # Pressed/selected states
    BG_QUATERNARY = "#3A3A3C"        # Borders, dividers, disabled
    
    # Text layers (with opacity)
    TEXT_PRIMARY = "#FFFFFF"         # 100%
    TEXT_SECONDARY = "#EBEBF599"     # 60% - section headers, descriptions
    TEXT_TERTIARY = "#EBEBF54D"      # 30% - placeholders
    TEXT_QUATERNARY = "#EBEBF52E"    # 18% - subtle hints
    
    # Accent colors
    ACCENT_BLUE = "#007AFF"          # Primary action
    ACCENT_BLUE_HOVER = "#0066CC"
    ACCENT_BLUE_PRESSED = "#0052A3"
    
    ACCENT_GREEN = "#34C759"         # Success
    ACCENT_GREEN_HOVER = "#28A745"
    
    ACCENT_RED = "#FF3B30"           # Error/Destructive
    ACCENT_RED_HOVER = "#CC2E26"
    
    ACCENT_ORANGE = "#FF9F0A"        # Warning
    ACCENT_PURPLE = "#AF52DE"        # Special
    
    # Semantic
    CARD_BG = BG_SECONDARY
    CARD_BORDER = BG_QUATERNARY
    SEPARATOR = BG_QUATERNARY
    
    # Shadows (subtle for dark mode)
    SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 4px 8px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 8px 16px rgba(0,0,0,0.5)"


class iOSSpacing:
    """8pt grid system."""
    SPACING_1 = 4
    SPACING_2 = 8
    SPACING_3 = 12
    SPACING_4 = 16
    SPACING_5 = 20
    SPACING_6 = 24
    SPACING_8 = 32
    SPACING_10 = 40
    SPACING_12 = 48


class iOSRadius:
    """Border radius values."""
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 14
    RADIUS_XL = 16
    RADIUS_2XL = 20
    RADIUS_FULL = 9999


class iOSTypography:
    """iOS-style font hierarchy using Inter font."""
    
    @staticmethod
    def get_font(size: int, weight: int = 400, italic: bool = False):
        """Get Inter font with specified parameters."""
        font = QFont("Inter", size)
        font.setWeight(QFont.Weight(weight))
        font.setItalic(italic)
        # Fallback chain
        font.setStyleHint(QFont.StyleHint.SansSerif)
        font.setFamilies(["Inter", "-apple-system", "BlinkMacSystemFont", 
                          "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"])
        return font
    
    # Font hierarchy (size, weight)
    LARGE_TITLE = (34, 700)      # Bold
    TITLE_1 = (28, 700)          # Bold
    TITLE_2 = (22, 700)          # Bold
    TITLE_3 = (20, 600)          # SemiBold
    HEADLINE = (17, 600)         # SemiBold
    BODY = (17, 400)             # Regular
    CALLOUT = (16, 400)          # Regular
    SUBHEADLINE = (15, 400)      # Regular
    FOOTNOTE = (13, 400)         # Regular
    CAPTION_1 = (12, 400)        # Regular
    CAPTION_2 = (11, 400)        # Regular


def load_inter_font():
    """Load Inter font from resources. Returns True if successful."""
    # Font files should be in src/gui/fonts/Inter-VariableFont_slnt,wght.ttf
    font_paths = [
        ":/fonts/Inter-VariableFont_slnt,wght.ttf",
        ":/fonts/Inter-Italic-VariableFont_slnt,wght.ttf"
    ]
    
    for path in font_paths:
        font_id = QFontDatabase.addApplicationFont(path)
        if font_id == -1:
            # Try filesystem fallback
            fs_path = path.replace(":/fonts/", "src/gui/fonts/")
            if os.path.exists(fs_path):
                font_id = QFontDatabase.addApplicationFont(fs_path)
        if font_id == -1:
            return False
    
    families = QFontDatabase.applicationFontFamilies(font_id)
    return "Inter" in families or len(families) > 0


def apply_new_theme(app):
    """Apply the new iOS-style theme to the application."""
    if not is_theme_enabled():
        return False
    
    # Load Inter font
    load_inter_font()
    
    # Set default font
    default_font = iOSTypography.get_font(*iOSTypography.BODY)
    app.setFont(default_font)
    
    # Apply global stylesheet
    stylesheet = generate_global_stylesheet()
    app.setStyleSheet(stylesheet)
    
    return True


def generate_global_stylesheet():
    """Generate the global QSS stylesheet for the new theme."""
    c = iOSColors
    s = iOSSpacing
    r = iOSRadius
    
    return f"""
/* === GLOBAL BASE === */
QWidget {{
    color: {c.TEXT_PRIMARY};
    background-color: {c.BG_PRIMARY};
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 17px;
}}

QWidget:focus {{
    outline: none;
}}

QWidget[cls="central"] {{
    background-color: {c.BG_PRIMARY};
    border: 1px solid {c.CARD_BORDER};
    border-radius: 0px;
}}

/* === SCROLLBARS === */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0px;
}}
QScrollBar::handle {{
    background: {c.BG_QUATERNARY};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:hover {{
    background: {c.TEXT_TERTIARY};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    background: none;
    height: 0px;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}

/* === TOOLBUTTONS (Sidebar) === */
QToolButton {{
    background-color: {c.BG_SECONDARY};
    border: none;
    color: {c.TEXT_PRIMARY};
    font-size: 14px;
    min-height: 40px;
    icon-size: 22px;
    padding-left: {s.SPACING_4}px;
    padding-right: {s.SPACING_4}px;
    border-radius: {r.RADIUS_MD}px;
}}
QToolButton:hover {{
    background-color: {c.BG_TERTIARY};
}}
QToolButton:pressed {{
    background-color: {c.BG_QUATERNARY};
}}
QToolButton[cls="sidebarBtn"] {{
    background-color: transparent;
    icon-size: 24px;
    padding: {s.SPACING_2}px;
    min-height: 44px;
}}
QToolButton[cls="sidebarBtn"]:hover {{
    background-color: {c.BG_TERTIARY};
}}
QToolButton[cls="sidebarBtn"]:checked {{
    background-color: {c.ACCENT_BLUE};
    color: white;
}}

/* === CHECKBOX (iOS-style Switch) === */
QCheckBox {{
    spacing: {s.SPACING_3}px;
    font-size: 17px;
    color: {c.TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 51px;
    height: 31px;
    border-radius: 15.5px;
    border: 2px solid {c.CARD_BORDER};
    background-color: {c.BG_QUATERNARY};
}}
QCheckBox::indicator:checked {{
    background-color: {c.ACCENT_GREEN};
    border: 2px solid {c.ACCENT_GREEN};
}}
QCheckBox::indicator:checked:hover {{
    background-color: {c.ACCENT_GREEN_HOVER};
}}
QCheckBox::indicator:disabled {{
    background-color: {c.BG_QUATERNARY};
    border-color: {c.SEPARATOR};
}}
QCheckBox:disabled {{
    color: {c.TEXT_QUATERNARY};
}}

/* === RADIO BUTTON === */
QRadioButton {{
    spacing: {s.SPACING_3}px;
    font-size: 17px;
}}
QRadioButton::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 11px;
    border: 2px solid {c.CARD_BORDER};
    background-color: {c.BG_SECONDARY};
}}
QRadioButton::indicator:checked {{
    background-color: {c.ACCENT_BLUE};
    border: 6px solid {c.BG_SECONDARY};  /* Inner dot effect */
}}
QRadioButton::indicator:checked:hover {{
    background-color: {c.ACCENT_BLUE_HOVER};
}}

/* === LINE EDIT === */
QLineEdit {{
    border: 1px solid {c.CARD_BORDER};
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_PRIMARY};
    font-size: 17px;
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    border-radius: {r.RADIUS_MD}px;
    selection-background-color: {c.ACCENT_BLUE};
}}
QLineEdit:focus {{
    border: 2px solid {c.ACCENT_BLUE};
}}
QLineEdit:disabled {{
    background-color: {c.BG_TERTIARY};
    color: {c.TEXT_QUATERNARY};
    border-color: {c.SEPARATOR};
}}

/* === COMBO BOX === */
QComboBox {{
    border: 1px solid {c.CARD_BORDER};
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_PRIMARY};
    font-size: 17px;
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    border-radius: {r.RADIUS_MD}px;
    min-height: 44px;
}}
QComboBox:hover {{
    border-color: {c.TEXT_TERTIARY};
}}
QComboBox:focus {{
    border: 2px solid {c.ACCENT_BLUE};
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
    background-color: {c.BG_SECONDARY};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_MD}px;
    selection-background-color: {c.ACCENT_BLUE};
    selection-color: white;
    outline: none;
    padding: {s.SPACING_2}px;
}}

/* === SLIDER === */
QSlider::groove:horizontal {{
    background-color: {c.BG_QUATERNARY};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background-color: {c.ACCENT_BLUE};
    width: 28px;
    height: 28px;
    margin: -12px 0;
    border-radius: 14px;
}}
QSlider::handle:horizontal:hover {{
    background-color: {c.ACCENT_BLUE_HOVER};
}}
QSlider::handle:horizontal:pressed {{
    background-color: {c.ACCENT_BLUE_PRESSED};
}}

/* === PROGRESS BAR === */
QProgressBar {{
    border: none;
    background-color: {c.BG_QUATERNARY};
    border-radius: {r.RADIUS_SM}px;
    height: 8px;
    text-align: center;
    color: {c.TEXT_PRIMARY};
    font-size: 11px;
}}
QProgressBar::chunk {{
    background-color: {c.ACCENT_BLUE};
    border-radius: {r.RADIUS_SM}px;
}}

/* === LABELS === */
QLabel {{
    font-size: 17px;
    color: {c.TEXT_PRIMARY};
}}

QLabel[cls="sectionHeader"] {{
    color: {c.TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: {s.SPACING_2}px 0 {s.SPACING_1}px 0;
}}

QLabel[cls="caption"] {{
    color: {c.TEXT_TERTIARY};
    font-size: 13px;
}}

QLabel[cls="footnote"] {{
    color: {c.TEXT_SECONDARY};
    font-size: 13px;
}}

QLabel[cls="title"] {{
    color: {c.TEXT_PRIMARY};
    font-size: 28px;
    font-weight: 700;
}}

QLabel[cls="headline"] {{
    color: {c.TEXT_PRIMARY};
    font-size: 17px;
    font-weight: 600;
}}

/* === SEPARATOR LINE === */
QFrame[cls="separator"] {{
    background-color: {c.SEPARATOR};
    max-height: 1px;
    min-height: 1px;
}}

/* === GROUP BOX (Card) === */
QGroupBox[cls="card"] {{
    background-color: {c.CARD_BG};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_MD}px;
    margin-top: {s.SPACING_3}px;
    padding-top: {s.SPACING_4}px;
    font-weight: 600;
    font-size: 13px;
    color: {c.TEXT_SECONDARY};
}}
QGroupBox[cls="card"]::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {s.SPACING_4}px;
    padding: 0 {s.SPACING_2}px;
}}

/* === MESSAGE BOX === */
QMessageBox {{
    background-color: {c.BG_PRIMARY};
    color: {c.TEXT_PRIMARY};
}}
QMessageBox QLabel {{
    color: {c.TEXT_PRIMARY};
    font-size: 17px;
}}
QMessageBox QPushButton {{
    background-color: {c.BG_SECONDARY};
    color: {c.ACCENT_BLUE};
    border: 1px solid {c.ACCENT_BLUE};
    border-radius: {r.RADIUS_MD}px;
    padding: {s.SPACING_3}px {s.SPACING_5}px;
    min-width: 80px;
    font-size: 17px;
    font-weight: 600;
}}
QMessageBox QPushButton:hover {{
    background-color: {c.BG_TERTIARY};
}}
QMessageBox QPushButton:pressed {{
    background-color: {c.BG_QUATERNARY};
}}
QMessageBox QPushButton[cls="primary"] {{
    background-color: {c.ACCENT_BLUE};
    color: white;
    border: none;
}}
QMessageBox QPushButton[cls="primary"]:hover {{
    background-color: {c.ACCENT_BLUE_HOVER};
}}
QMessageBox QPushButton[cls="destructive"] {{
    background-color: {c.ACCENT_RED};
    color: white;
    border: none;
}}
QMessageBox QPushButton[cls="destructive"]:hover {{
    background-color: {c.ACCENT_RED_HOVER};
}}

/* === TOOLTIP === */
QToolTip {{
    background-color: {c.BG_TERTIARY};
    color: {c.TEXT_PRIMARY};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_SM}px;
    padding: {s.SPACING_2}px {s.SPACING_3}px;
    font-size: 13px;
}}

/* === TAB BAR === */
QTabBar::tab {{
    background-color: transparent;
    color: {c.TEXT_SECONDARY};
    padding: {s.SPACING_3}px {s.SPACING_5}px;
    border-bottom: 2px solid transparent;
    font-size: 15px;
    font-weight: 500;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {c.ACCENT_BLUE};
    border-bottom: 2px solid {c.ACCENT_BLUE};
}}
QTabBar::tab:hover:!selected {{
    color: {c.TEXT_TERTIARY};
}}

/* === SPIN BOX === */
QSpinBox, QDoubleSpinBox {{
    border: 1px solid {c.CARD_BORDER};
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_PRIMARY};
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    border-radius: {r.RADIUS_MD}px;
    min-height: 44px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {c.ACCENT_BLUE};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 32px;
    subcontrol-origin: border;
}}
QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}

/* === DISABLED STATE === */
QWidget:disabled {{
    color: {c.TEXT_QUATERNARY};
    background-color: {c.BG_TERTIARY};
}}

/* === CARD WIDGET === */
QFrame[cls="card"] {{
    background-color: {c.CARD_BG};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_MD}px;
}}

/* === BUTTON BASE === */
QPushButton, QToolButton[cls="button"] {{
    border: none;
    border-radius: {r.RADIUS_MD}px;
    padding: {s.SPACING_3}px {s.SPACING_5}px;
    font-size: 17px;
    font-weight: 600;
    min-height: 44px;
}}

QPushButton[cls="primary"], QToolButton[cls="primary"] {{
    background-color: {c.ACCENT_BLUE};
    color: white;
}}
QPushButton[cls="primary"]:hover, QToolButton[cls="primary"]:hover {{
    background-color: {c.ACCENT_BLUE_HOVER};
}}
QPushButton[cls="primary"]:pressed, QToolButton[cls="primary"]:pressed {{
    background-color: {c.ACCENT_BLUE_PRESSED};
}}

QPushButton[cls="secondary"], QToolButton[cls="secondary"] {{
    background-color: {c.BG_SECONDARY};
    color: {c.ACCENT_BLUE};
    border: 1px solid {c.ACCENT_BLUE};
}}
QPushButton[cls="secondary"]:hover, QToolButton[cls="secondary"]:hover {{
    background-color: {c.BG_TERTIARY};
}}

QPushButton[cls="destructive"], QToolButton[cls="destructive"] {{
    background-color: {c.ACCENT_RED};
    color: white;
}}
QPushButton[cls="destructive"]:hover, QToolButton[cls="destructive"]:hover {{
    background-color: {c.ACCENT_RED_HOVER};
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: {c.BG_QUATERNARY} !important;
    color: {c.TEXT_QUATERNARY} !important;
    border-color: {c.SEPARATOR} !important;
}}

/* === LIST WIDGET === */
QListWidget {{
    background-color: {c.BG_PRIMARY};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_MD}px;
    outline: none;
    padding: {s.SPACING_2}px;
}}
QListWidget::item {{
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    border-radius: {r.RADIUS_SM}px;
    margin: {s.SPACING_1}px {s.SPACING_2}px;
}}
QListWidget::item:selected {{
    background-color: {c.ACCENT_BLUE};
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: {c.BG_TERTIARY};
}}

/* === TREE WIDGET === */
QTreeWidget {{
    background-color: {c.BG_PRIMARY};
    border: 1px solid {c.CARD_BORDER};
    border-radius: {r.RADIUS_MD}px;
    outline: none;
    alternate-background-color: {c.BG_SECONDARY};
}}
QTreeWidget::item {{
    padding: {s.SPACING_3}px {s.SPACING_4}px;
}}
QTreeWidget::item:selected {{
    background-color: {c.ACCENT_BLUE};
    color: white;
}}
QHeaderView::section {{
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_SECONDARY};
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    border: none;
    border-bottom: 1px solid {c.CARD_BORDER};
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
}}

/* === DOCK WIDGET === */
QDockWidget {{
}}
QDockWidget::title {{
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_SECONDARY};
    padding: {s.SPACING_3}px {s.SPACING_4}px;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* === SPLITTER === */
QSplitter::handle {{
    background-color: {c.CARD_BORDER};
    width: 1px;
    height: 1px;
}}
QSplitter::handle:hover {{
    background-color: {c.ACCENT_BLUE};
}}

/* === STATUS BAR === */
QStatusBar {{
    background-color: {c.BG_SECONDARY};
    color: {c.TEXT_SECONDARY};
    border-top: 1px solid {c.CARD_BORDER};
    font-size: 13px;
}}
"""