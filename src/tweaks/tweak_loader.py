from .tweaks import tweaks, TweakID
from .tweak_classes import BasicPlistTweak, FileLocation, AdvancedPlistTweak, NullifyFileTweak


def _load_once(sentinel: TweakID, additional_tweaks: dict):
    if sentinel in tweaks:
        return
    tweaks.update(additional_tweaks)


def load_internal():
    _load_once(TweakID.RTL, {
        TweakID.SBBuildNumber: BasicPlistTweak(
            FileLocation.globalPreferences,
            "UIStatusBarShowBuildVersion"
        ),
        TweakID.RTL: BasicPlistTweak(
            FileLocation.globalPreferences,
            "NSForceRightToLeftWritingDirection"
        ),
        TweakID.LTR: BasicPlistTweak(
            FileLocation.globalPreferences,
            "NSForceLeftToRightWritingDirection"
        ),
        TweakID.SBIconVisibility: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBIconVisibility"
        ),
        TweakID.MetalForceHudEnabled: BasicPlistTweak(
            FileLocation.globalPreferences,
            "MetalForceHudEnabled"
        ),
        TweakID.iMessageDiagnosticsEnabled: BasicPlistTweak(
            FileLocation.globalPreferences,
            "iMessageDiagnosticsEnabled"
        ),
        TweakID.IDSDiagnosticsEnabled: BasicPlistTweak(
            FileLocation.globalPreferences,
            "IDSDiagnosticsEnabled"
        ),
        TweakID.VCDiagnosticsEnabled: BasicPlistTweak(
            FileLocation.globalPreferences,
            "VCDiagnosticsEnabled"
        ),
        TweakID.AccessoryDeveloperEnabled: BasicPlistTweak(
            FileLocation.globalPreferences,
            "AccessoryDeveloperEnabled"
        ),
        TweakID.DisableSecondsHand: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisableClockIconSecondsHand"
        ),
        TweakID.DisableSearchingWebsites: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBSearchDisabledDomains"
        ),
        TweakID.ShowButtonHints: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBHardwareButtonHintDropletsAlwaysVisibleInSnapshots"
        ),
        TweakID.AppStoreDebug: BasicPlistTweak(
            FileLocation.appStore,
            "debugGestureEnabled"
        ),
        TweakID.NotesDebugMode: BasicPlistTweak(
            FileLocation.notes,
            "DebugModeEnabled"
        ),
        TweakID.BKDigitizerVisualizeTouches: BasicPlistTweak(
            FileLocation.backboardd,
            "BKDigitizerVisualizeTouches"
        ),
        TweakID.BKHideAppleLogoOnLaunch: BasicPlistTweak(
            FileLocation.backboardd,
            "BKHideAppleLogoOnLaunch"
        ),
        TweakID.EnableWakeGestureHaptic: BasicPlistTweak(
            FileLocation.coreMotion,
            "EnableWakeGestureHaptic"
        ),
        TweakID.PlaySoundOnPaste: BasicPlistTweak(
            FileLocation.pasteboard,
            "PlaySoundOnPaste"
        ),
        TweakID.AnnounceAllPastes: BasicPlistTweak(
            FileLocation.pasteboard,
            "AnnounceAllPastes"
        )
    })


def load_liquidglass():
    _load_once(TweakID.DisableSolarium, {
        TweakID.ForceSolariumFallback: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SolariumForceFallback"
        ),
        TweakID.DisableSolarium: BasicPlistTweak(
            FileLocation.globalPreferences,
            "com.apple.SwiftUI.DisableSolarium"
        ),
        TweakID.IgnoreSolariumLinkedOnCheck: BasicPlistTweak(
            FileLocation.globalPreferences,
            "com.apple.SwiftUI.IgnoreSolariumLinkedOnCheck"
        ),
        TweakID.NoLiquidClock: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisallowGlassTime"
        ),
        TweakID.NoLiquidDock: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisableGlassDock"
        ),
        TweakID.DisableSpecularMotion: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisableSpecularEverywhereUsingLSSAssertion"
        ),
        TweakID.DisableOuterRefraction: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SolariumDisableOuterRefraction"
        ),
        TweakID.DisableSolariumHDR: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SolariumAllowHDR",
            value=False
        ),
        # === iOS 27 additions ===
        TweakID.DisallowGlassButtons: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisallowGlassButtons"
        ),
        TweakID.DisallowGlassLockScreen: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisallowGlassLockScreen"
        ),
        TweakID.ForceEnhancedSpeculars: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SolariumForceEnhancedSpeculars"
        ),
        TweakID.ForceSolariumIntelligence: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SolariumForceIntelligence"
        ),
        TweakID.UISolariumFallback: BasicPlistTweak(
            FileLocation.globalPreferences,
            "UISolariumForceFallback"
        ),
        TweakID.IgnoreSolariumHardwareCheck: BasicPlistTweak(
            FileLocation.globalPreferences,
            "com.apple.SwiftUI.IgnoreSolariumHardwareCheck"
        ),
        TweakID.IgnoreSolariumOptOut: BasicPlistTweak(
            FileLocation.globalPreferences,
            "com.apple.SwiftUI.IgnoreSolariumOptOut"
        ),
        TweakID.DisableSpecularEverywhere: BasicPlistTweak(
            FileLocation.globalPreferences,
            "SBDisableSpecularEverywhere"
        )
    })


def load_springboard():
    _load_once(TweakID.LockScreenFootnote, {
        TweakID.LockScreenFootnote: BasicPlistTweak(
            FileLocation.footnote,
            key="LockScreenFootnote", value=""
        ),
        TweakID.WatchOSCompatibility: AdvancedPlistTweak(
            file_location=FileLocation.nanoregistry,
            keyValues={
                "IOS_PAIRING_EOL_MIN_PAIRING_COMPATIBILITY_VERSION_CHIPIDS": "",
                "maxPairingCompatibilityVersion": 37,
                "lastRestoreIdentifier": "CD97EEB8-BCD2-486B-BC13-C384E6B916C4", # not sure if this is needed
                "minPairingCompatibilityVersionWithChipID": 1,
                "lastRestoreIdentifier_state": 0,
                "AdvertisingIdentifierSeed": "85E70251-1960-4DA0-A321-B68AC118FAB5", # this prolly isn't needed either
                "minPairingCompatibilityVersion": 1
            }
        ),
        TweakID.AirDropDisableTimeLimit: BasicPlistTweak(
            FileLocation.airdrop,
            "OverrideTimeLimitEveryoneMode"
        ),
        TweakID.SBDontLockAfterCrash: BasicPlistTweak(
            FileLocation.springboard,
            "SBDontLockAfterCrash"
        ),
        TweakID.SBDontDimOrLockOnAC: BasicPlistTweak(
            FileLocation.springboard,
            "SBDontDimOrLockOnAC"
        ),
        TweakID.SBHideLowPowerAlerts: BasicPlistTweak(
            FileLocation.springboard,
            "SBHideLowPowerAlerts"
        ),
        TweakID.SBHideACPower: BasicPlistTweak(
            FileLocation.springboard,
            "SBHideACPower"
        ),
        TweakID.SBNeverBreadcrumb: BasicPlistTweak(
            FileLocation.springboard,
            "SBNeverBreadcrumb"
        ),
        TweakID.SBShowSupervisionTextOnLockScreen: BasicPlistTweak(
            FileLocation.springboard,
            "SBShowSupervisionTextOnLockScreen"
        ),
        TweakID.AirplaySupport: BasicPlistTweak(
            FileLocation.springboard,
            "SBExtendedDisplayOverrideSupportForAirPlayAndDontFileRadars"
        ),
        TweakID.SBMinimumLockscreenIdleTime: BasicPlistTweak(
            FileLocation.springboard,
            key="SBMinimumLockscreenIdleTime",
            value=5
        ),
        TweakID.SBAlwaysShowSystemApertureInSnapshots: BasicPlistTweak(
            FileLocation.springboard,
            "SBAlwaysShowSystemApertureInSnapshots"
        ),
        TweakID.HideDICompletely: BasicPlistTweak(
            FileLocation.springboard,
            "SBSuppressDynamicIslandCompletely"
        ),
        TweakID.SBShowAuthenticationEngineeringUI: BasicPlistTweak(
            FileLocation.springboard,
            "SBShowAuthenticationEngineeringUI"
        ),
        TweakID.UseFloatingTabBar: BasicPlistTweak(
            FileLocation.uikit,
            key="UseFloatingTabBar",
            value=False
        )
    })


def load_daemons():
    _load_once(TweakID.Daemons, {
        TweakID.Daemons: AdvancedPlistTweak(
            FileLocation.disabledDaemons,
            {
                "com.apple.magicswitchd.companion": True,
                "com.apple.security.otpaird": True,
                "com.apple.dhcp6d": True,
                "com.apple.bootpd": True,
                "com.apple.ftp-proxy-embedded": False,
                "com.apple.relevanced": True
            },
            owner=0, group=0
        ),
        TweakID.ClearScreenTimeAgentPlist: NullifyFileTweak(FileLocation.screentime),
    })