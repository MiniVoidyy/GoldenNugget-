#! python3

import subprocess
import sys
import asyncio

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.mobile_config import MobileConfigService

SKIP_ALL_PANES = [
    'Location',
    'Restore',
    'SIMSetup',
    'Android',
    'AppleID',
    'IntendedUser',
    'Siri',
    'ScreenTime',
    'Diagnostics',
    'SoftwareUpdate',
    'Passcode',
    'Biometric',
    'Payment',
    'Zoom',
    'DisplayTone',
    'MessagingActivationUsingPhoneNumber',
    'HomeButtonSensitivity',
    'CloudStorage',
    'ScreenSaver',
    'TapToSetup',
    'Keyboard',
    'PreferredLanguage',
    'SpokenLanguage',
    'WatchMigration',
    'OnBoarding',
    'TVProviderSignIn',
    'TVHomeScreenSync',
    'Privacy',
    'TVRoom',
    'iMessageAndFaceTime',
    'AppStore',
    'Safety',
    'Multitasking',
    'ActionButton',
    'Intelligence',
    'CameraButton',
    'TermsOfAddress',
    'AccessibilityAppearance',
    'Welcome',
    'Appearance',
    'RestoreCompleted',
    'UpdateCompleted',
    'WebContentFiltering',
    'SafetyAndHandling',
]

async def apply_skip_all_setup(udid: str | None = None):
    ld = await create_using_usbmux(serial=udid)
    try:
        async with MobileConfigService(lockdown=ld) as mcs:
            cloud_config = await mcs.get_cloud_configuration() or {}
            cloud_config['SkipSetup'] = list(SKIP_ALL_PANES)
            await mcs.set_cloud_configuration(cloud_config)
    finally:
        try:
            await ld.close()
        except Exception:
            pass

def main(argv: list[str]):
    asyncio.run(argv[1])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: skip_setup.py <UUID>")
        exit(1)
    main(sys.argv)