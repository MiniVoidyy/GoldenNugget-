from enum import Enum

class FileLocation(Enum):
    # Feature Flags
    featureflags = "/var/preferences/FeatureFlags/Global.plist"
    
    # SpringBoard Options
    springboard = "/var/Managed Preferences/mobile/com.apple.springboard.plist"
    springboardHomeDomain = "/var/mobile/Library/Preferences/com.apple.springboard.plist"
    footnote = "/var/containers/Shared/SystemGroup/systemgroup.com.apple.configurationprofiles/Library/ConfigurationProfiles/SharedDeviceConfiguration.plist"
    footnoteHomeDomain = "/var/mobile/Library/Preferences/SharedDeviceConfiguration.plist"
    airdrop = "/var/Managed Preferences/mobile/com.apple.sharingd.plist"
    airdropHomeDomain = "/var/mobile/Library/Preferences/com.apple.sharingd.plist"
    nanoregistry = "/var/mobile/Library/Preferences/com.apple.NanoRegistry.plist"
      
    # Internal Options
    globalPreferences = "/var/Managed Preferences/mobile/.GlobalPreferences.plist"
    globalPreferencesHomeDomain = "/var/mobile/Library/Preferences/.GlobalPreferences.plist"
    appStore = "/var/Managed Preferences/mobile/com.apple.AppStore.plist"
    appStoreHomeDomain = "/var/mobile/Library/Preferences/com.apple.AppStore.plist"
    backboardd = "/var/Managed Preferences/mobile/com.apple.backboardd.plist"
    backboarddHomeDomain = "/var/mobile/Library/Preferences/com.apple.backboardd.plist"
    coreMotion = "/var/Managed Preferences/mobile/com.apple.CoreMotion.plist"
    coreMotionHomeDomain = "/var/mobile/Library/Preferences/com.apple.CoreMotion.plist"
    pasteboard = "/var/Managed Preferences/mobile/com.apple.Pasteboard.plist"
    pasteboardHomeDomain = "/var/mobile/Library/Preferences/com.apple.Pasteboard.plist"
    notes = "/var/Managed Preferences/mobile/com.apple.mobilenotes.plist"
    notesHomeDomain = "/var/mobile/Library/Preferences/com.apple.mobilenotes.plist"
    uikit = "/var/Managed Preferences/mobile/com.apple.UIKit.plist"
    uikitHomeDomain = "/var/mobile/Library/Preferences/com.apple.UIKit.plist"

    # Daemons
    disabledDaemons = "/var/db/com.apple.xpc.launchd/disabled.plist"
    screentime = "/var/mobile/Library/Preferences/com.apple.ScreenTimeAgent.plist"
