import re
from typing import Optional, Callable

from PySide6.QtCore import QCoreApplication

from src.exceptions.nugget_exception import NuggetException
from .basic_plist_locations import FileLocation

_on_tweak_change: Optional[Callable[[], None]] = None

def set_tweak_change_callback(callback: Optional[Callable[[], None]]):
    """Register a callback to be invoked when any tweak changes."""
    global _on_tweak_change
    _on_tweak_change = callback

def _notify_tweak_change():
    if _on_tweak_change:
        try:
            _on_tweak_change()
        except Exception:
            pass  # Never let callback errors break tweak changes

class Tweak:
    def __init__(
            self,
            key: str,
            value: any = 1,
            owner: int = 501, group: int = 501
        ):
        self.key = key
        self.value = value
        self.owner = owner
        self.group = group
        self.enabled = False

    def set_enabled(self, value: bool):
        if self.enabled != value:
            self.enabled = value
            _notify_tweak_change()
    def toggle_enabled(self):
        self.enabled = not self.enabled
        _notify_tweak_change()
    def set_value(self, new_value: any, toggle_enabled: bool = True):
        self.value = new_value
        if toggle_enabled:
            self.enabled = True
        _notify_tweak_change()

    def apply_tweak(self):
        raise NotImplementedError
    
class NullifyFileTweak(Tweak):
    def __init__(
            self,
            file_location: FileLocation,
            owner: int = 501, group: int = 501
        ):
        super().__init__(key=None, value=None, owner=owner, group=group)
        self.file_location = file_location

    def apply_tweak(self, other_tweaks: dict):
        if self.enabled:
            other_tweaks[self.file_location] = b""
    

class BasicPlistTweak(Tweak):
    def __init__(
            self,
            file_location: FileLocation,
            key: str,
            value: any = True,
            owner: int = 501, group: int = 501,
            is_risky: bool = False
        ):
        super().__init__(key=key, value=value, owner=owner, group=group)
        self.file_location = file_location
        self.is_risky = is_risky

    def apply_tweak(self, other_tweaks: dict, risky_allowed: bool = False) -> dict:
        if not self.enabled or (self.is_risky and not risky_allowed):
            return other_tweaks
        if self.file_location in other_tweaks:
            other_tweaks[self.file_location][self.key] = self.value
        else:
            other_tweaks[self.file_location] = {self.key: self.value}
        return other_tweaks
    
class AdvancedPlistTweak(BasicPlistTweak):
    def __init__(
        self,
        file_location: FileLocation,
        keyValues: dict,
        owner: int = 501, group: int = 501,
        is_risky: bool = False
    ):
        super().__init__(file_location=file_location, key=None, value=keyValues, owner=owner, group=group, is_risky=is_risky)

    def set_multiple_values(self, keys: list[str], value: any):
        for key in keys:
            self.value[key] = value

    def apply_tweak(self, other_tweaks: dict, risky_allowed: bool = False) -> dict:
        if not self.enabled or (self.is_risky and not risky_allowed):
            return other_tweaks
        plist = {}
        for key in self.value:
            plist[key] = self.value[key]
        other_tweaks[self.file_location] = plist
        return other_tweaks


class FeatureFlagTweak(Tweak):
    def __init__(
            self,
                flag_category: str, flag_names: list,
                is_list: bool=True, inverted: bool=False
            ):
        super().__init__(key=None)
        self.flag_category = flag_category
        self.flag_names = flag_names
        self.is_list = is_list
        self.inverted = inverted
        
    def apply_tweak(self, plist: dict):
        to_enable = self.enabled
        if self.inverted:
            to_enable = not self.enabled
        # create the category list if it doesn't exist
        if not self.flag_category in plist:
            plist[self.flag_category] = {}
        for flag in self.flag_names:
            if self.is_list:
                plist[self.flag_category][flag] = {
                    'Enabled': to_enable
                }
            else:
                plist[self.flag_category][flag] = to_enable
        return plist
