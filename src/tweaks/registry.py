"""Single source of truth for the plist-based tweaks.

Every tweak's definition (id, section, title, plist location, key, default
value, UI kind) lives here exactly once. ``tweak_loader`` builds the runtime
instances from these specs and the iOS tweaks page renders its rows from
them — adding a tweak means adding one entry here.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import QT_TRANSLATE_NOOP

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
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    iphone_only: bool = False
    ipad_only: bool = False
    factory: Optional[Callable[[], object]] = None  # overrides BasicPlistTweak
    help: str = ""  # hover tooltip, e.g. what Toggle ON does to performance


def _t(id_: TweakID, section: Section, title: str, location: FileLocation,
       key: str, **kwargs) -> TweakSpec:
    # QT_TRANSLATE_NOOP marks the title for pyside6-lupdate; the actual
    # translation happens at render time (translators are not installed yet
    # when this module is imported). The optional ``help`` tooltip goes
    # through the same marker so translators can localize it too.
    if kwargs.get("help"):
        kwargs["help"] = QT_TRANSLATE_NOOP("Nugget", kwargs["help"])
    return TweakSpec(id=id_, section=section,
                     title=QT_TRANSLATE_NOOP("Nugget", title),
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
    _t(TweakID.ForceSolariumFallback, Section.LIQUID_GLASS, "Force Solarium Fallback", GP, "SolariumForceFallback", min_version="26.0",
       help="Toggle ON: forces Liquid Glass to render through its lighter fallback look instead of the full glass effect. Increases performance, at the cost of some liquid-glass visuals."),
    _t(TweakID.IgnoreSolariumLinkedOnCheck, Section.LIQUID_GLASS, "Ignore Solarium Linked-On Check", GP, "com.apple.SwiftUI.IgnoreSolariumLinkedOnCheck", min_version="26.0",
       help="Toggle ON: enables Liquid Glass on apps that were not built/updated for it. Decreases performance, because more surfaces render with glass."),
    _t(TweakID.ForceSolariumIntelligence, Section.LIQUID_GLASS, "Force Solarium Intelligence", GP, "SolariumForceIntelligence", min_version="27.0",
       help="Toggle ON: forces the full Liquid Glass 'intelligence' pipeline even where iOS would normally use the lighter look. Decreases performance."),
    _t(TweakID.ForceEnhancedSpeculars, Section.LIQUID_GLASS, "Force Enhanced Speculars", GP, "SolariumForceEnhancedSpeculars", min_version="27.0",
       help="Toggle ON: uses the higher-quality specular (shiny) reflections on every glass surface. Decreases performance."),
    _t(TweakID.UISolariumFallback, Section.LIQUID_GLASS, "UI Solarium Fallback", GP, "UISolariumForceFallback", min_version="27.0",
       help="Toggle ON: forces user-interface surfaces to render with the lighter Solarium fallback appearance. Increases performance."),
    _t(TweakID.IgnoreSolariumHardwareCheck, Section.LIQUID_GLASS, "Ignore Solarium Hardware Check", GP, "com.apple.SwiftUI.IgnoreSolariumHardwareCheck", min_version="27.0",
       help="Toggle ON: ignores the GPU/hardware capability check and shows Liquid Glass even on devices below the performance bar. Decreases performance."),
    _t(TweakID.IgnoreSolariumOptOut, Section.LIQUID_GLASS, "Ignore Solarium Opt-Out", GP, "com.apple.SwiftUI.IgnoreSolariumOptOut", min_version="27.0",
       help="Toggle ON: ignores apps that opted out of Liquid Glass and renders glass in them anyway. Decreases performance."),
    _t(TweakID.DisallowGlassButtons, Section.LIQUID_GLASS, "Disallow Glass Buttons", GP, "SBDisallowGlassButtons", min_version="27.0",
       help="Toggle ON: keeps buttons in their classic non-glass look instead of Liquid Glass. Slightly increases performance."),
    _t(TweakID.DisallowGlassLockScreen, Section.LIQUID_GLASS, "Disallow Glass Lock Screen", GP, "SBDisallowGlassLockScreen", min_version="27.0",
       help="Toggle ON: renders the Lock Screen without Liquid Glass styling. Slightly increases performance."),
    _t(TweakID.DisableSpecularEverywhere, Section.LIQUID_GLASS, "Disable Specular Everywhere", GP, "SBDisableSpecularEverywhere", min_version="27.0",
       help="Toggle ON: disables specular (shiny) reflections on all Liquid Glass surfaces. Increases performance."),
    _t(TweakID.NoLiquidClock, Section.LIQUID_GLASS, "Disable Liquid Glass on LS Clock", GP, "SBDisallowGlassTime", min_version="26.0",
       help="Toggle ON: removes Liquid Glass from the Lock Screen clock. Slightly increases performance."),
    _t(TweakID.NoLiquidDock, Section.LIQUID_GLASS, "Disable Liquid Glass on Dock", GP, "SBDisableGlassDock", min_version="26.0",
       help="Toggle ON: removes Liquid Glass from the Home Screen dock. Slightly increases performance."),
    _t(TweakID.DisableSpecularMotion, Section.LIQUID_GLASS, "Disable Specular Motion", GP, "SBDisableSpecularEverywhereUsingLSSAssertion", min_version="26.0",
       help="Toggle ON: disables the moving light reflection that sweeps across Liquid Glass surfaces. Increases performance."),
    _t(TweakID.DisableOuterRefraction, Section.LIQUID_GLASS, "Disable Outer Refraction", GP, "SolariumDisableOuterRefraction", min_version="26.0",
       help="Toggle ON: removes the frosted-glass background refraction around Liquid Glass edges. Increases performance."),
    _t(TweakID.DisableSolariumHDR, Section.LIQUID_GLASS, "Disable Solarium HDR", GP, "SolariumAllowHDR", value=False, min_version="26.0",
       help="Toggle ON: turns off HDR rendering in Liquid Glass (writes SolariumAllowHDR = false). Increases performance and improves battery life on OLED screens."),

    # --- SpringBoard ---
    _t(TweakID.LockScreenFootnote, Section.SPRINGBOARD, "Lock Screen Footnote Text",
       FileLocation.footnote, "LockScreenFootnote", value="", kind=Kind.TEXT,
       help="Set a custom text line shown under the clock on the Lock Screen. Leave empty to remove it."),
    _t(TweakID.WatchOSCompatibility, Section.SPRINGBOARD, "Allow pairing with any watchOS version",
       FileLocation.nanoregistry, "", factory=_watchos_compatibility, ipad_only=True,
       help="Toggle ON: bypasses the watchOS pairing compatibility check so watches running newer watchOS can pair with this device. iPad-only."),
    _t(TweakID.AirDropDisableTimeLimit, Section.SPRINGBOARD, "Disable AirDrop Time Limit for Everyone Option",
       FileLocation.airdrop, "OverrideTimeLimitEveryoneMode",
       help="Toggle ON: adds a permanent 'Everyone' AirDrop option and removes the 10-minute time limit when it is selected."),
    _t(TweakID.SBDontLockAfterCrash, Section.SPRINGBOARD, "Disable Lock After Respring",
       FileLocation.springboard, "SBDontLockAfterCrash",
       help="Toggle ON: the device no longer locks (and asks for the passcode) after the UI crashes and resprings."),
    _t(TweakID.SBDontDimOrLockOnAC, Section.SPRINGBOARD, "Disable Screen Dimming While Charging",
       FileLocation.springboard, "SBDontDimOrLockOnAC",
       help="Toggle ON: the screen no longer dims or auto-locks while the device is charging."),
    _t(TweakID.SBHideLowPowerAlerts, Section.SPRINGBOARD, "Disable Low Battery Alerts",
       FileLocation.springboard, "SBHideLowPowerAlerts",
       help="Toggle ON: suppresses the low-battery pop-up alerts at 20% and 10%."),
    _t(TweakID.SBHideACPower, Section.SPRINGBOARD, "Hide AC Power on Lock Screen",
       FileLocation.springboard, "SBHideACPower",
       help="Toggle ON: hides the charging/power source indicator from the Lock Screen."),
    _t(TweakID.SBNeverBreadcrumb, Section.SPRINGBOARD, "Disable Breadcrumbs",
       FileLocation.springboard, "SBNeverBreadcrumb",
       help="Toggle ON: stops the 'Back to [App]' banner that appears when you return from another app."),
    _t(TweakID.SBShowSupervisionTextOnLockScreen, Section.SPRINGBOARD, "Show Supervision Text on Lock Screen",
       FileLocation.springboard, "SBShowSupervisionTextOnLockScreen",
       help="Toggle ON: shows supervision status text on the Lock Screen, useful on supervised devices."),
    _t(TweakID.AirplaySupport, Section.SPRINGBOARD, "Enable AirPlay support for Stage Manager",
       FileLocation.springboard, "SBExtendedDisplayOverrideSupportForAirPlayAndDontFileRadars",
       help="Toggle ON: allows using AirPlay displays with Stage Manager / external displays."),
    _t(TweakID.SBMinimumLockscreenIdleTime, Section.SPRINGBOARD, "Auto‑Lock (Lock Screen)",
       FileLocation.springboard, "SBMinimumLockscreenIdleTime", value=5, kind=Kind.NUMBER,
       min_value=0, max_value=600,
       help="Set how many seconds of idle time on the Lock Screen before the screen locks automatically (0 = never)."),
    _t(TweakID.SBAlwaysShowSystemApertureInSnapshots, Section.SPRINGBOARD, "Show Dynamic Island in Screenshots",
       FileLocation.springboard, "SBAlwaysShowSystemApertureInSnapshots", min_version="17.4", iphone_only=True,
       help="Toggle ON: the Dynamic Island stays visible in screenshots and app-switcher snapshots instead of being hidden. iPhone-only."),
    _t(TweakID.HideDICompletely, Section.SPRINGBOARD, "Hide Dynamic Island Completely",
       FileLocation.springboard, "SBSuppressDynamicIslandCompletely", min_version="17.4", iphone_only=True,
       help="Toggle ON: removes the Dynamic Island pill from the UI entirely. iPhone-only."),
    _t(TweakID.SBShowAuthenticationEngineeringUI, Section.SPRINGBOARD, "Show Red/Green Authentication Line on Lock Screen",
       FileLocation.springboard, "SBShowAuthenticationEngineeringUI",
       help="Toggle ON: shows the red/green engineering authentication line on the Lock Screen (debug indicator)."),
    _t(TweakID.UseFloatingTabBar, Section.SPRINGBOARD, "Disable Floating Tab Bar",
       FileLocation.uikit, "UseFloatingTabBar", value=False, ipad_only=True,
       help="Toggle ON: disables the floating tab bar in iPad apps and restores the classic fixed tab bar. iPad-only."),

    # --- Internal Options ---
    _t(TweakID.SBBuildNumber, Section.INTERNAL, "Show Build Version in Status Bar", GP, "UIStatusBarShowBuildVersion",
       help="Toggle ON: adds the iOS build number (e.g. 22A5270) next to the version in the Status Bar."),
    _t(TweakID.RTL, Section.INTERNAL, "Force Right-to-Left Layout", GP, "NSForceRightToLeftWritingDirection",
       help="Toggle ON: forces the entire system UI into a right-to-left layout."),
    _t(TweakID.LTR, Section.INTERNAL, "Force Left-to-Right Layout", GP, "NSForceLeftToRightWritingDirection",
       help="Toggle ON: forces the entire system UI into a left-to-right layout (undoes forced RTL)."),
    _t(TweakID.SBIconVisibility, Section.INTERNAL, "Show Hidden Icons on Home Screen", GP, "SBIconVisibility",
       help="Toggle ON: reveals Home Screen apps that are normally hidden by the system."),
    _t(TweakID.iMessageDiagnosticsEnabled, Section.INTERNAL, "iMessage Debugging", GP, "iMessageDiagnosticsEnabled",
       help="Toggle ON: enables iMessage internal diagnostics/debugging for developers."),
    _t(TweakID.IDSDiagnosticsEnabled, Section.INTERNAL, "Continuity Debugging", GP, "IDSDiagnosticsEnabled",
       help="Toggle ON: exposes Continuity (IDS) internal diagnostics settings."),
    _t(TweakID.VCDiagnosticsEnabled, Section.INTERNAL, "FaceTime Debugging", GP, "VCDiagnosticsEnabled",
       help="Toggle ON: enables FaceTime internal diagnostics/debugging for developers."),
    _t(TweakID.AccessoryDeveloperEnabled, Section.INTERNAL, "Show Accessory Developer Settings", GP, "AccessoryDeveloperEnabled",
       help="Toggle ON: shows the accessory (MFi) developer settings in the Settings app."),
    _t(TweakID.DisableSecondsHand, Section.INTERNAL, "Disable Clock Icon Seconds Hand", GP, "SBDisableClockIconSecondsHand",
       help="Toggle ON: stops the ticking seconds hand on the Home Screen clock icon."),
    _t(TweakID.DisableSearchingWebsites, Section.INTERNAL, "Disable Spotlight Searching in Websites", GP, "SBSearchDisabledDomains",
       help="Toggle ON: prevents Spotlight from searching website content."),
    _t(TweakID.ShowButtonHints, Section.INTERNAL, "Show Hardware Button Hints in Screenshots", GP, "SBHardwareButtonHintDropletsAlwaysVisibleInSnapshots",
       help="Toggle ON: renders hardware button hint overlays inside screenshots."),
    _t(TweakID.AppStoreDebug, Section.INTERNAL, "App Store Debug Gesture", FileLocation.appStore, "debugGestureEnabled",
       help="Toggle ON: enables the App Store hidden debug gesture (long-press on the profile icon)."),
    _t(TweakID.NotesDebugMode, Section.INTERNAL, "Notes Debug Mode", FileLocation.notes, "DebugModeEnabled",
       help="Toggle ON: enables the Notes app hidden debug mode."),
    _t(TweakID.BKDigitizerVisualizeTouches, Section.INTERNAL, "Show Touches With Debug Info", FileLocation.backboardd, "BKDigitizerVisualizeTouches",
       help="Toggle ON: draws touch points on screen with additional debug information."),
    _t(TweakID.BKHideAppleLogoOnLaunch, Section.INTERNAL, "Hide Respring Icon", FileLocation.backboardd, "BKHideAppleLogoOnLaunch",
       help="Toggle ON: hides the Apple logo shown on screen during a respring or reboot."),
    _t(TweakID.EnableWakeGestureHaptic, Section.INTERNAL, "Vibrate on Raise-to-Wake", FileLocation.coreMotion, "EnableWakeGestureHaptic",
       help="Toggle ON: plays a haptic vibration when the device is raised to wake."),
    _t(TweakID.PlaySoundOnPaste, Section.INTERNAL, "Play Sound on Paste", FileLocation.pasteboard, "PlaySoundOnPaste",
       help="Toggle ON: plays a sound whenever something is pasted."),
    _t(TweakID.AnnounceAllPastes, Section.INTERNAL, "Show Notifications for System Pastes", FileLocation.pasteboard, "AnnounceAllPastes",
       help="Toggle ON: shows a notification banner for every paste, including system-initiated ones."),
)

SPECS_BY_SECTION = {section: [s for s in SPECS if s.section == section] for section in Section}
SPECS_BY_ID = {spec.id: spec for spec in SPECS}