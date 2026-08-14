from enum import Enum

from src.devicemanagement.constants import Version

class Page(Enum):
    Home = 0
    Gestalt = 1
    FeatureFlags = 2
    EUEnabler = 3
    StatusBar = 4
    Springboard = 5
    InternalOptions = 6
    LiquidGlass = 7
    Daemons = 8
    Posterboard = 9
    Templates = 10
    Passcode = 11
    RiskyTweaks = 12
    Tweaks = 13
    Apply = 14
    Settings = 15

    def getPageName(self) -> str:
        name_map = [
            "Home",
            "Mobile Gestalt",
            "Feature Flags",
            "Eligibility",
            "Status Bar",
            "Springboard",
            "Internal",
            "Liquid Glass",
            "Daemons",
            "PosterBoard",
            "Templates",
            "Passcode",
            "Resolution Modifications",
            "Tweaks",
            "Apply",
            "Settings"
        ]
        return name_map[self.value]

def get_resettable_pages(device_manager) -> list[Page]:
    device_ver = Version(device_manager.get_current_device_version())
    page_list: list[Page] = [Page.Springboard, Page.InternalOptions, Page.Daemons]

    # Status Bar is broken on iOS 27 (no write permissions for Speakeasy flags)
    # so the feature is hidden on iOS 27+
    if device_ver < Version("27.0"):
        page_list.insert(0, Page.StatusBar)

    # add the exploit related pages
    if not device_manager.get_current_device_patched():
        page_list.insert(0, Page.FeatureFlags)
        page_list.insert(0, Page.Gestalt)

    return page_list