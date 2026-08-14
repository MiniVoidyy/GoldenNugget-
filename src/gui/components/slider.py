"""
iOS-style Slider component.
"""

from PySide6.QtWidgets import QSlider, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

from ..theme import iOSColors, is_theme_enabled


class iOSSlider(QSlider):
    """iOS-style slider with custom thumb."""
    
    valueChanged = Signal(int)
    
    def __init__(self, minimum=0, maximum=100, value=0, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        if not is_theme_enabled():
            return
            
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.valueChanged.connect(self.valueChanged.emit)
        
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background-color: {iOSColors.BG_QUATERNARY};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background-color: #007AFF;
                width: 28px;
                height: 28px;
                margin: -12px 0;
                border-radius: 14px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: #0066CC;
            }}
            QSlider::handle:horizontal:pressed {{
                background-color: #0052A3;
            }}
            QSlider::sub-page:horizontal {{
                background-color: #007AFF;
                border-radius: 2px;
            }}
        """)


class iOSSliderRow(QWidget):
    """Slider with label and value display."""
    
    valueChanged = Signal(int)
    
    def __init__(self, title="", minimum=0, maximum=100, value=0, 
                 value_suffix="", show_value=True, parent=None):
        super().__init__()
        
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt
        
        if not is_theme_enabled():
            return
            
        self.value_suffix = value_suffix
        self.show_value = show_value
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Title row
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 17px;
            font-weight: 400;
        """)
        header_layout.addWidget(self.title_label)
        
        if show_value:
            self.value_label = QLabel(f"{value}{value_suffix}")
            self.value_label.setStyleSheet("""
                color: #EBEBF599;
                font-size: 17px;
                font-weight: 500;
                font-variant-numeric: tabular-nums;
            """)
            header_layout.addWidget(self.value_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # Slider
        self.slider = iOSSlider()
        self.slider.valueChanged.connect(self._on_value_changed)
        main_layout.addWidget(self.slider)
    
    def _on_value_changed(self, value):
        if self.show_value:
            self.value_label.setText(f"{value}{self.value_suffix}")
        self.valueChanged.emit(value)
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)