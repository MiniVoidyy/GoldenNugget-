from typing import Optional, Callable

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
            owner: int = 501, group: int = 501
        ):
        super().__init__(key=key, value=value, owner=owner, group=group)
        self.file_location = file_location

    def apply_tweak(self, other_tweaks: dict) -> dict:
        if not self.enabled:
            return other_tweaks
        if self.file_location in other_tweaks:
            other_tweaks[self.file_location][self.key] = self.value
        else:
            other_tweaks[self.file_location] = {self.key: self.value}
        return other_tweaks


class ReversibleBooleanPlistTweak(BasicPlistTweak):
    """Write both states so disabling a previously applied key takes effect."""

    def __init__(self, file_location, key, *, integer_value=False):
        super().__init__(file_location, key)
        self.integer_value = integer_value

    def apply_tweak(self, other_tweaks: dict, force_disabled: bool = False) -> dict:
        target = other_tweaks.get(self.file_location)
        if not isinstance(target, dict):
            target = {}
            other_tweaks[self.file_location] = target
        value = False if force_disabled else bool(self.enabled)
        target[self.key] = int(value) if self.integer_value else value
        return other_tweaks

class ExperimentalBooleanPlistTweak(ReversibleBooleanPlistTweak):
    """Leave untouched keys alone; persist explicit off selections for rollback."""

    def __init__(self, location, key, on_value, off_value):
        super().__init__(location, key)
        self.on_value = on_value
        self.off_value = off_value
        self.value = None

    def set_enabled(self, value: bool):
        value = bool(value)
        if self.enabled != value:
            self.value = self.on_value if value else self.off_value
        super().set_enabled(value)

    def apply_tweak(self, other_tweaks: dict, force_disabled: bool = False) -> dict:
        if not self.enabled and self.value is None:
            return other_tweaks
        value = self.on_value if self.enabled and not force_disabled else self.off_value
        other_tweaks.setdefault(self.file_location, {})[self.key] = value
        return other_tweaks


class DynamicIslandBorderWriteTest(ExperimentalBooleanPlistTweak):
    VALUES = {
        "keyLineEnabled": False,
        "activityKeyLineColorEnabled": False,
        "keyLineAlpha": 0.0,
        "keyLineThickness": 0.0,
        "backgroundBlurEnabled": False,
        "elementShadowEnabled": False,
        "sensorShadowVisible": False,
    }

    def __init__(self):
        super().__init__(FileLocation.springboard, "keyLineEnabled", True, False)

    def apply_tweak(self, other_tweaks: dict, force_disabled: bool = False) -> dict:
        if not self.enabled and self.value is None:
            return other_tweaks
        target = other_tweaks.setdefault(self.file_location, {})
        if self.enabled and not force_disabled:
            target.update(self.VALUES)
        else:
            for key in self.VALUES:
                target.pop(key, None)
        return other_tweaks


class ResettableNumericPreferenceTweak(BasicPlistTweak):
    """Use -1 to remove an optional numeric key from the replacement plist."""

    def apply_tweak(self, other_tweaks: dict) -> dict:
        if not self.enabled:
            return other_tweaks
        target = other_tweaks.setdefault(self.file_location, {})
        if self.value == -1:
            target.pop(self.key, None)
        else:
            target[self.key] = float(self.value)
        return other_tweaks


class OptionalBundlePreferenceTweak(BasicPlistTweak):
    """An empty app identifier removes the key from the generated preference file."""

    def apply_tweak(self, other_tweaks: dict) -> dict:
        if not self.enabled:
            return other_tweaks
        target = other_tweaks.setdefault(self.file_location, {})
        if self.value:
            target[self.key] = self.value
        else:
            target.pop(self.key, None)
        return other_tweaks

    
class CompanionKeyTweak(BasicPlistTweak):
    """A plist tweak that writes companion keys alongside its main key.

    Some settings only take effect once the system can see that a human
    changed them (e.g. ``UIViewGlassEverEditedInSettings`` marks the Liquid
    Glass tint amount as deliberately chosen; without it iOS treats the
    amount as never set and applies its own default). Those keys are not
    user-facing toggles, so they ride along with the real one.

    Merging matches ``BasicPlistTweak``, so several tweaks can keep sharing
    one plist (both this one and ``UseFloatingTabBar`` target the UIKit
    Managed Preferences file).
    """
    def __init__(
            self,
            file_location: FileLocation,
            key: str,
            value: any = True,
            companion_keys: Optional[dict] = None,
            owner: int = 501, group: int = 501
        ):
        super().__init__(file_location=file_location, key=key, value=value,
                         owner=owner, group=group)
        self.companion_keys = dict(companion_keys or {})

    def apply_tweak(self, other_tweaks: dict) -> dict:
        if not self.enabled:
            return other_tweaks
        target = other_tweaks.get(self.file_location)
        if not isinstance(target, dict):
            target = {}
            other_tweaks[self.file_location] = target
        target[self.key] = self.value
        target.update(self.companion_keys)
        return other_tweaks

class AdvancedPlistTweak(BasicPlistTweak):
    def __init__(
        self,
        file_location: FileLocation,
        keyValues: dict,
        owner: int = 501, group: int = 501,
        never_enable: Optional[set] = None,
        allowed_keys: Optional[set] = None
    ):
        super().__init__(file_location=file_location, key=None, value=keyValues, owner=owner, group=group)
        self.never_enable = set(never_enable or ())
        # If set, only keys in this set are ever applied / stored (interface-
        # visible daemons). Keys outside it are dropped, never written.
        self.allowed_keys = set(allowed_keys) if allowed_keys is not None else None

    def _filter_keys(self, values: dict) -> dict:
        """Drop keys that are hard-protected or not interface-visible."""
        out = {}
        for key, value in values.items():
            if key in self.never_enable:
                continue
            if self.allowed_keys is not None and key not in self.allowed_keys:
                continue
            out[key] = value
        return out

    def set_multiple_values(self, keys: list[str], value: any):
        for key in keys:
            if value and value is not False and value is not None and key in self.never_enable:
                continue  # hard-protected: this key must never be enabled
            if self.allowed_keys is not None and key not in self.allowed_keys:
                continue  # not exposed in the UI: never introduce it
            self.value[key] = value
        _notify_tweak_change()

    def apply_tweak(self, other_tweaks: dict) -> dict:
        if not self.enabled:
            return other_tweaks
        other_tweaks[self.file_location] = self._filter_keys(self.value)
        return other_tweaks


class DaemonPlistTweak(AdvancedPlistTweak):
    def apply_tweak(self, other_tweaks: dict) -> dict:
        other_tweaks = super().apply_tweak(other_tweaks)
        if not self.enabled:
            return other_tweaks
        from .daemons_tweak import Daemon
        values = self._filter_keys(self.value)
        if not any(key in values for key in Daemon.OTA.value):
            return other_tweaks
        target = other_tweaks.setdefault(FileLocation.ota, {})
        if any(values.get(key) is True for key in Daemon.OTA.value):
            target["MobileAssetSUAllowOSVersionChange"] = False
        else:
            target.pop("MobileAssetSUAllowOSVersionChange", None)
        return other_tweaks
