"""Single source of truth for the plist-based tweaks.

Every tweak's definition (id, section, title, plist location, key, default
value, UI kind) lives here exactly once. ``tweak_loader`` builds the runtime
instances from these specs and the iOS tweaks page renders its rows from
them — adding a tweak means adding one entry here.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import QCoreApplication

from .basic_plist_locations import FileLocation
from .tweak_names import TweakID


class Section(Enum):
    LIQUID_GLASS = "Liquid Glass"
    SPRINGBOARD = "SpringBoard"
    INTERNAL = "Internal Options"


class Kind(Enum):
    SWITCH = "switch"   # boolean toggle
    TEXT = "text"       # free-form text value
    NUMBER = "number"   # numeric value


@dataclass(frozen=True)
class TweakSpec:
    id: TweakID
    section: Section
    title: str
    location: FileLocation
    key: str
    value: any = True          # value written when the tweak is enabled
    kind: Kind = Kind.SWITCH
    min_value: int = 0         # NUMBER kind only
    max_value: int = 999       # NUMBER kind only
    factory: Optional[Callable[[], object]] = None  # overrides BasicPlistTweak


def _t(id_: TweakID, section: Section, title: str, location: FileLocation,
       key: str, **kwargs) -> TweakSpec:
    return TweakSpec(id=id_, section=section,
                     title=QCoreApplication.translate("Nugget", title),
                     location=location, key=key, **kwargs)


def _watchos_compatibility():
    from .tweak_classes import AdvancedPlistTweak
    return AdvancedPlistTweak(
        FileLocation.nanoregistry,
        keyValues={
            "IOS_PAIRING_EOL_MIN_PAIRING_COMPATIBILITY_VERSION_CHIPIDS": "",
            "maxPairingCompatibilityVersion": 37,
            "lastRestoreIdentifier": "CD97EEB8-BCD2-486B-BC13-C384E6B916C4",  # not sure if this is needed
            "minPairingCompatibilityVersionWithChipID": 1,
            "lastRestoreIdentifier_state": 0,
            "AdvertisingIdentifierSeed": "85E70251-1960-4DA0-A321-B68AC118FAB5",  # this prolly isn't needed either
            "minPairingCompatibilityVersion": 1
        })


GP = FileLocation.globalPreferences

SPECS: tuple[TweakSpec, ...] = (
    # --- Liquid Glass ---
    _t(TweakID.ForceSolariumFallback, Section.LIQUID_GLASS, "Force Solarium Fallback", GP, "SolariumForceFallback"),
    _t(TweakID.IgnoreSolariumLinkedOnCheck, Section.LIQUID_GLASS, "Ignore Solarium Linked-On Check", GP, "com.apple.SwiftUI.IgnoreSolariumLinkedOnCheck"),
    _t(TweakID.ForceSolariumIntelligence, Section.LIQUID_GLASS, "Force Solarium Intelligence", GP, "SolariumForceIntelligence"),
    _t(TweakID.ForceEnhancedSpeculars, Section.LIQUID_GLASS, "Force Enhanced Speculars", GP, "SolariumForceEnhancedSpeculars"),
    _t(TweakID.UISolariumFallback, Section.LIQUID_GLASS, "UI Solarium Fallback", GP, "UISolariumForceFallback"),
    _t(TweakID.IgnoreSolariumHardwareCheck, Section.LIQUID_GLASS, "Ignore Solarium Hardware Check", GP, "com.apple.SwiftUI.IgnoreSolariumHardwareCheck"),
    _t(TweakID.IgnoreSolariumOptOut, Section.LIQUID_GLASS, "Ignore Solarium Opt-Out", GP, "com.apple.SwiftUI.IgnoreSolariumOptOut"),
    _t(TweakID.DisallowGlassButtons, Section.LIQUID_GLASS, "Disallow Glass Buttons", GP, "SBDisallowGlassButtons"),
    _t(TweakID.DisallowGlassLockScreen, Section.LIQUID_GLASS, "Disallow Glass Lock Screen", GP, "SBDisallowGlassLockScreen"),
    _t(TweakID.DisableSpecularEverywhere, Section.LIQUID_GLASS, "Disable Specular Everywhere", GP, "SBDisableSpecularEverywhere"),
    _t(TweakID.NoLiquidClock, Section.LIQUID_GLASS, "Disable Liquid Glass on LS Clock", GP, "SBDisallowGlassTime"),
    _t(TweakID.NoLiquidDock, Section.LIQUID_GLASS, "Disable Liquid Glass on Dock", GP, "SBDisableGlassDock"),
    _t(TweakID.DisableSpecularMotion, Section.LIQUID_GLASS, "Disable Specular Motion", GP, "SBDisableSpecularEverywhereUsingLSSAssertion"),
    _t(TweakID.DisableOuterRefraction, Section.LIQUID_GLASS, "Disable Outer Refraction", GP, "SolariumDisableOuterRefraction"),
    _t(TweakID.DisableSolariumHDR, Section.LIQUID_GLASS, "Disable Solarium HDR", GP, "SolariumAllowHDR", value=False),

    # --- SpringBoard ---
    _t(TweakID.LockScreenFootnote, Section.SPRINGBOARD, "Lock Screen Footnote Text",
       FileLocation.footnote, "LockScreenFootnote", value="", kind=Kind.TEXT),
    _t(TweakID.WatchOSCompatibility, Section.SPRINGBOARD, "Allow pairing with any watchOS version",
       FileLocation.nanoregistry, "", factory=_watchos_compatibility),
    _t(TweakID.AirDropDisableTimeLimit, Section.SPRINGBOARD, "Disable AirDrop Time Limit for Everyone Option",
       FileLocation.airdrop, "OverrideTimeLimitEveryoneMode"),
    _t(TweakID.SBDontLockAfterCrash, Section.SPRINGBOARD, "Disable Lock After Respring",
       FileLocation.springboard, "SBDontLockAfterCrash"),
    _t(TweakID.SBDontDimOrLockOnAC, Section.SPRINGBOARD, "Disable Screen Dimming While Charging",
       FileLocation.springboard, "SBDontDimOrLockOnAC"),
    _t(TweakID.SBHideLowPowerAlerts, Section.SPRINGBOARD, "Disable Low Battery Alerts",
       FileLocation.springboard, "SBHideLowPowerAlerts"),
    _t(TweakID.SBHideACPower, Section.SPRINGBOARD, "Hide AC Power on Lock Screen",
       FileLocation.springboard, "SBHideACPower"),
    _t(TweakID.SBNeverBreadcrumb, Section.SPRINGBOARD, "Disable Breadcrumbs",
       FileLocation.springboard, "SBNeverBreadcrumb"),
    _t(TweakID.SBShowSupervisionTextOnLockScreen, Section.SPRINGBOARD, "Show Supervision Text on Lock Screen",
       FileLocation.springboard, "SBShowSupervisionTextOnLockScreen"),
    _t(TweakID.AirplaySupport, Section.SPRINGBOARD, "Enable AirPlay support for Stage Manager",
       FileLocation.springboard, "SBExtendedDisplayOverrideSupportForAirPlayAndDontFileRadars"),
    _t(TweakID.SBMinimumLockscreenIdleTime, Section.SPRINGBOARD, "Auto‑Lock (Lock Screen)",
       FileLocation.springboard, "SBMinimumLockscreenIdleTime", value=5, kind=Kind.NUMBER,
       min_value=0, max_value=600),
    _t(TweakID.SBAlwaysShowSystemApertureInSnapshots, Section.SPRINGBOARD, "Show Dynamic Island in Screenshots",
       FileLocation.springboard, "SBAlwaysShowSystemApertureInSnapshots"),
    _t(TweakID.HideDICompletely, Section.SPRINGBOARD, "Hide Dynamic Island Completely",
       FileLocation.springboard, "SBSuppressDynamicIslandCompletely"),
    _t(TweakID.SBShowAuthenticationEngineeringUI, Section.SPRINGBOARD, "Show Red/Green Authentication Line on Lock Screen",
       FileLocation.springboard, "SBShowAuthenticationEngineeringUI"),
    _t(TweakID.UseFloatingTabBar, Section.SPRINGBOARD, "Disable Floating Tab Bar",
       FileLocation.uikit, "UseFloatingTabBar", value=False),

    # --- Internal Options ---
    _t(TweakID.SBBuildNumber, Section.INTERNAL, "Show Build Version in Status Bar", GP, "UIStatusBarShowBuildVersion"),
    _t(TweakID.RTL, Section.INTERNAL, "Force Right-to-Left Layout", GP, "NSForceRightToLeftWritingDirection"),
    _t(TweakID.LTR, Section.INTERNAL, "Force Left-to-Right Layout", GP, "NSForceLeftToRightWritingDirection"),
    _t(TweakID.SBIconVisibility, Section.INTERNAL, "Show Hidden Icons on Home Screen", GP, "SBIconVisibility"),
    _t(TweakID.iMessageDiagnosticsEnabled, Section.INTERNAL, "iMessage Debugging", GP, "iMessageDiagnosticsEnabled"),
    _t(TweakID.IDSDiagnosticsEnabled, Section.INTERNAL, "Continuity Debugging", GP, "IDSDiagnosticsEnabled"),
    _t(TweakID.VCDiagnosticsEnabled, Section.INTERNAL, "FaceTime Debugging", GP, "VCDiagnosticsEnabled"),
    _t(TweakID.AccessoryDeveloperEnabled, Section.INTERNAL, "Show Accessory Developer Settings", GP, "AccessoryDeveloperEnabled"),
    _t(TweakID.DisableSecondsHand, Section.INTERNAL, "Disable Clock Icon Seconds Hand", GP, "SBDisableClockIconSecondsHand"),
    _t(TweakID.DisableSearchingWebsites, Section.INTERNAL, "Disable Spotlight Searching in Websites", GP, "SBSearchDisabledDomains"),
    _t(TweakID.ShowButtonHints, Section.INTERNAL, "Show Hardware Button Hints in Screenshots", GP, "SBHardwareButtonHintDropletsAlwaysVisibleInSnapshots"),
    _t(TweakID.AppStoreDebug, Section.INTERNAL, "App Store Debug Gesture", FileLocation.appStore, "debugGestureEnabled"),
    _t(TweakID.NotesDebugMode, Section.INTERNAL, "Notes Debug Mode", FileLocation.notes, "DebugModeEnabled"),
    _t(TweakID.BKDigitizerVisualizeTouches, Section.INTERNAL, "Show Touches With Debug Info", FileLocation.backboardd, "BKDigitizerVisualizeTouches"),
    _t(TweakID.BKHideAppleLogoOnLaunch, Section.INTERNAL, "Hide Respring Icon", FileLocation.backboardd, "BKHideAppleLogoOnLaunch"),
    _t(TweakID.EnableWakeGestureHaptic, Section.INTERNAL, "Vibrate on Raise-to-Wake", FileLocation.coreMotion, "EnableWakeGestureHaptic"),
    _t(TweakID.PlaySoundOnPaste, Section.INTERNAL, "Play Sound on Paste", FileLocation.pasteboard, "PlaySoundOnPaste"),
    _t(TweakID.AnnounceAllPastes, Section.INTERNAL, "Show Notifications for System Pastes", FileLocation.pasteboard, "AnnounceAllPastes"),
)

SPECS_BY_SECTION = {section: [s for s in SPECS if s.section == section] for section in Section}
SPECS_BY_ID = {spec.id: spec for spec in SPECS}