"""
iOS-style reusable components for GoldenNugget.
"""

from .card import iOSCard, iOSCardSection
from .switch import iOSSwitch, iOSSwitchRow
from .button import iOSButton, iOSToolButton, iOSButtonRow
from .section import iOSSectionHeader, iOSSectionFooter
from .input import iOSLineEdit, iOSComboBox, iOSPasswordLineEdit, iOSTextEdit
from .slider import iOSSlider, iOSSliderRow
from .progress import iOSProgressBar, iOSProgressBarWithLabel
from .label import iOSLabel, iOSSectionHeader, iOSSectionFooter
from .tweaks_page import iOSTweakRow, iOSTweakSection, iOSTweaksPage, create_default_tweaks_page

__all__ = [
    "create_default_tweaks_page",
    "iOSCard",
    "iOSCardSection",
    "iOSSwitch",
    "iOSSwitchRow",
    "iOSButton",
    "iOSToolButton",
    "iOSButtonRow",
    "iOSSectionHeader",
    "iOSSectionFooter",
    "iOSLineEdit",
    "iOSComboBox",
    "iOSPasswordLineEdit",
    "iOSTextEdit",
    "iOSSlider",
    "iOSSliderRow",
    "iOSProgressBar",
    "iOSProgressBarWithLabel",
    "iOSLabel",
    "iOSSectionHeader",
    "iOSSectionFooter",
    "iOSTweakRow",
    "iOSTweakSection",
    "iOSTweaksPage",
]