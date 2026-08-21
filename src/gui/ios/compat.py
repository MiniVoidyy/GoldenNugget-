from src.devicemanagement.constants import Version
from src.tweaks.tweaks import TweakID


# Minimum iOS version required for a tweak to make sense.
TWEAK_MIN_VERSION = {
    # Liquid Glass (iOS 26+)
    TweakID.ForceSolariumFallback: "26.0",
    TweakID.IgnoreSolariumLinkedOnCheck: "26.0",
    TweakID.NoLiquidClock: "26.0",
    TweakID.NoLiquidDock: "26.0",
    TweakID.DisableSpecularMotion: "26.0",
    TweakID.DisableOuterRefraction: "26.0",
    TweakID.DisableSolariumHDR: "26.0",
    # iOS 27 additions
    TweakID.DisallowGlassButtons: "27.0",
    TweakID.DisallowGlassLockScreen: "27.0",
    TweakID.ForceEnhancedSpeculars: "27.0",
    TweakID.ForceSolariumIntelligence: "27.0",
    TweakID.UISolariumFallback: "27.0",
    TweakID.IgnoreSolariumHardwareCheck: "27.0",
    TweakID.IgnoreSolariumOptOut: "27.0",
    TweakID.DisableSpecularEverywhere: "27.0",
    # Dynamic Island options (iOS 17.4+)
    TweakID.SBAlwaysShowSystemApertureInSnapshots: "17.4",
    TweakID.HideDICompletely: "17.4",
    # PosterBoard stuff
    TweakID.PosterBoard: "17.4",
    TweakID.Templates: "17.4",
}

# Tweak is only useful on iPads.
IPAD_ONLY_TWEAKS = {
    TweakID.UseFloatingTabBar,
    TweakID.WatchOSCompatibility,
}

# Tweak is only useful on iPhones.
IPHONE_ONLY_TWEAKS = {
    TweakID.HideDICompletely,
    TweakID.SBAlwaysShowSystemApertureInSnapshots,
}


def is_tweak_compatible(tweak_id: TweakID, device_version: str, is_iphone: bool) -> bool:
    """Return True if the tweak makes sense on the given device."""
    if device_version:
        try:
            ver = Version(device_version)
        except Exception:
            ver = None
        if ver is not None:
            min_ver = TWEAK_MIN_VERSION.get(tweak_id)
            if min_ver and ver < Version(min_ver):
                return False
    if tweak_id in IPAD_ONLY_TWEAKS and is_iphone:
        return False
    if tweak_id in IPHONE_ONLY_TWEAKS and not is_iphone:
        return False
    return True
