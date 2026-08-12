"""Headless run 7: disable the Speakeasy status bar -> classic fallback.

Arms every writable Speakeasy-disable surface (see
_inject_speakeasy_disable in src/restore/restore.py) plus the classic
Library/SpringBoard/statusBarOverrides payload:

- HomeDomain prefs: com.apple.springboard.plist, com.apple.SpringBoard.plist,
  com.apple.UIKit.plist, com.apple.FeatureFlags.plist (4 flags: Speakeasy,
  SpeakeasyNewStatusBar, SpeakeasyAttributionManager,
  SpeakeasyStatusBarWindowRotation, all {Enabled: false})
- ManagedPreferencesDomain MCX plists: mobile/com.apple.springboard.plist,
  mobile/com.apple.UIKit.plist (4 bool keys = false)
- SystemPreferencesDomain new file FeatureFlags/Settings.plist
  ({SpringBoard: {<flag>: {Enabled: false}}} — the only path
  FeatureFlags.framework reads, /var/preferences/FeatureFlags/Settings.plist)

Usage:
    python3 tools/test_status_bar_carrier7.py [carrier_name]
"""

import asyncio
import os
import plistlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.usbmux import list_devices

from src.gui.main_window import MainWindow  # noqa: F401
from src.controllers.settings import Settings
from src.devicemanagement.constants import Device
from src.devicemanagement.device_manager import DeviceManager
from src.restore.restore import FileToRestore
from src.tweaks.tweaks import tweaks, TweakID


async def main() -> int:
    carrier = sys.argv[1] if len(sys.argv) > 1 else "awesomenull"

    devices = await list_devices()
    usb = [d for d in devices if d.is_usb]
    if not usb:
        print("ERROR: no USB device connected")
        return 1
    serial = usb[0].serial

    ld = await create_using_usbmux(serial=serial, autopair=True)
    try:
        vals = dict(ld.all_values)
    finally:
        await ld.close()

    dev = Device(
        udid=serial, usb=True, name=vals["DeviceName"],
        version=vals["ProductVersion"], build=vals["BuildVersion"],
        model=vals["ProductType"], hardware=vals["HardwareModel"],
        cpu=vals["HardwarePlatform"], locale="en_US",
        books_container_uuid="",
    )
    print(f"Device: {dev.name} ({dev.model}, {dev.hardware}) iOS {dev.version} ({dev.build})")

    dm = DeviceManager()
    dm.pref_manager.settings = Settings("settings")
    dm.data_singleton.current_device = dev
    dm.data_singleton.device_available = True
    dm.data_singleton.gestalt_path = None

    for t in tweaks.values():
        t.enabled = False

    sb = tweaks[TweakID.StatusBar]
    sb.set_enabled(True)
    sb.set_carrier_override(carrier)

    classic_bytes = bytes(sb.setter.get_data())
    print(f"[classic] statusBarOverrides: {len(classic_bytes)} bytes, "
          f"carrier={sb.get_carrier_override()!r}")

    flags = {
        "SpringBoard": {
            "Speakeasy": {"Enabled": False},
            "SpeakeasyNewStatusBar": {"Enabled": False},
            "SpeakeasyAttributionManager": {"Enabled": False},
            "SpeakeasyStatusBarWindowRotation": {"Enabled": False},
        },
    }
    print("[flags] Speakeasy*=OFF x4")

    files = [
        FileToRestore(
            contents=classic_bytes,
            restore_path="Library/SpringBoard/statusBarOverrides",
            domain="HomeDomain",
        ),
        FileToRestore(
            contents=plistlib.dumps(flags),
            restore_path="Library/Preferences/com.apple.FeatureFlags.plist",
            domain="HomeDomain",
        ),
        FileToRestore(
            contents=plistlib.dumps(flags),
            restore_path="/private/var/preferences/FeatureFlags/Settings.plist",
            domain="",
        ),
        FileToRestore(
            contents=plistlib.dumps(flags),
            restore_path="/private/var/preferences/FeatureFlags/Global.plist",
            domain="",
        ),
    ]

    print("\n[start] three-phase protective backup path "
          "(incl. _inject_speakeasy_disable surfaces):")
    final_alert = await dm.start_restore(
        files, use_bookrestore=False,
        update_label=lambda x: print("   ", x))
    print("RESULT:", final_alert.txt if final_alert else None)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))