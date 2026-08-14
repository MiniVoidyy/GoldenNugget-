import sys
from enum import Enum
from packaging.version import Version

# When launched with --enable-legacy-support, all iOS version restrictions are
# lifted so the fork can be used on old versions at the user's own risk.
LEGACY_SUPPORT_ENABLED = "--enable-legacy-support" in sys.argv

class Device:
    def __init__(self, 
                udid: int, usb: bool, name: str,
                version: str, build: str,
                model: str, hardware: str, cpu: str, locale: str,
                books_container_uuid: str
            ):
        self.udid = udid
        self.connected_via_usb = usb
        self.name = name
        self.version = version
        self.build = build
        self.model = model
        self.hardware = hardware
        self.cpu = cpu
        self.locale = locale
        self.books_container_uuid = books_container_uuid

    def is_exploit_fully_patched(self) -> bool:
        return True

    def has_bookrestore(self) -> bool:
        return False

    def has_partial_sparserestore(self) -> bool:
        return False

    def has_exploit(self) -> bool:
        return True

    def supported(self) -> bool:
        return True

    def is_supported_by_fork(self) -> bool:
        return is_supported_by_fork(self.version)

def is_supported_by_fork(version: str) -> bool:
    if LEGACY_SUPPORT_ENABLED:
        return True
    # this fork only supports iOS 26.2 and newer (the iOS 27 era)
    return Version(version) > Version("26.1")

class Tweak(Enum):
    StatusBar = 'Status Bar'
    SpringboardOptions = 'SpringBoard Options'
    InternalOptions = 'Internal Options'
    SkipSetup = 'Setup Options'

class FileLocation(Enum):
    # Control Center
    mute = "ControlCenter/ManagedPreferencesDomain/mobile/com.apple.control-center.MuteModule.plist"
    focus = "ControlCenter/ManagedPreferencesDomain/mobile/com.apple.FocusUIModule.plist"
    spoken = "ControlCenter/ManagedPreferencesDomain/mobile/com.apple.siri.SpokenNotificationsModule.plist"
    module_config = "ControlCenter/HomeDomain/Library/ControlCenter/ModuleConfiguration.plist"
    replay_kit_audio = "ControlCenter/ManagedPreferencesDomain/mobile/com.apple.replaykit.AudioConferenceControlCenterModule.plist"
    replay_kit_video = "ControlCenter/ManagedPreferencesDomain/mobile/com.apple.replaykit.VideoConferenceControlCenterModule.plist"

    # Status Bar
    status_bar = "StatusBar/HomeDomain/Library/SpringBoard/statusBarOverrides"
    
    # SpringBoard Options
    springboard = "SpringboardOptions/ManagedPreferencesDomain/mobile/com.apple.springboard.plist"
    footnote = "SpringboardOptions/ConfigProfileDomain/Library/ConfigurationProfiles/SharedDeviceConfiguration.plist"
    wifi = "SpringboardOptions/SystemPreferencesDomain/SystemConfiguration/com.apple.wifi.plist"
    uikit = "SpringboardOptions/ManagedPreferencesDomain/mobile/com.apple.UIKit.plist"
    accessibility = "SpringboardOptions/ManagedPreferencesDomain/mobile/com.apple.Accessibility.plist"
    wifi_debug = "SpringboardOptions/ManagedPreferencesDomain/mobile/com.apple.MobileWiFi.debug.plist"
    airdrop = "SpringboardOptions/ManagedPreferencesDomain/mobile/com.apple.sharingd.plist"
    
    # Internal Options
    global_prefs = "InternalOptions/ManagedPreferencesDomain/mobile/hiddendotGlobalPreferences.plist"
    app_store = "InternalOptions/ManagedPreferencesDomain/mobile/com.apple.AppStore.plist"
    backboardd = "InternalOptions/ManagedPreferencesDomain/mobile/com.apple.backboardd.plist"
    core_motion = "InternalOptions/ManagedPreferencesDomain/mobile/com.apple.CoreMotion.plist"
    pasteboard = "InternalOptions/HomeDomain/Library/Preferences/com.apple.Pasteboard.plist"
    notes = "InternalOptions/ManagedPreferencesDomain/mobile/com.apple.mobilenotes.plist"
    maps = "InternalOptions/AppDomain-com.apple.Maps/Library/Preferences/com.apple.Maps.plist"
    weather = "InternalOptions/AppDomain-com.apple.weather/Library/Preferences/com.apple.weather.plist"
    
    # Setup Options
    cloud_config = "SkipSetup/ConfigProfileDomain/Library/ConfigurationProfiles/CloudConfigurationDetails.plist"