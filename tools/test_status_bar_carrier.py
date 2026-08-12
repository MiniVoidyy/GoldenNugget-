"""Headless test: apply the carrier override via the three-phase protective
backup path (no Books app required).

iOS 27 status bar investigation (from DSC reverse engineering):

- SpringBoard checks ``isEnabled("SpringBoard", "Speakeasy")`` OR
  ``isEnabled("SpringBoard", "SpeakeasyNewStatusBar")`` (0x2242963e8).
  Enabling either flag switches the status bar to the NEW Speakeasy system,
  which reads an NSKeyedArchiver'ed archive — the classic
  ``Library/SpringBoard/statusBarOverrides`` binary struct file is ignored.
- UIKit (chunk .01, offset 0x636E1E5) still contains the legacy path string
  ``Library/SpringBoard/statusBarOverrides`` — the classic format is the
  fallback when the new mechanism is NOT active.

So the strategy is the inverse of the earlier FeatureFlags payloads:

1. DISABLE both gates (``Speakeasy`` and ``SpeakeasyNewStatusBar``) in
   ``HomeDomain/Library/Preferences/com.apple.FeatureFlags.plist`` → the new
   Speakeasy status bar is inactive → legacy path is used.
2. Drop the classic binary ``HomeDomain/Library/SpringBoard/statusBarOverrides``
   (raw StatusBarOverrideData struct from the C setter) carrying the carrier
   override "awesomenull" — this is the file UIKit's legacy fallback reads.

Both paths ride the proven HomeDomain backup injection
(``_HOME_DOMAIN_TWEAK_PATHS`` in restore.py).

Usage:
    python3 tools/test_status_bar_carrier.py [carrier_name]
"""

import asyncio
import os
import plistlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.usbmux import list_devices

# Import in the same order as main_app.py — device_manager alone trips a
# pre-existing circular import (preference_manager <-> bookrestore).
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

    # make sure only the status bar tweak is applied
    for t in tweaks.values():
        t.enabled = False

    sb = tweaks[TweakID.StatusBar]
    sb.set_enabled(True)
    sb.set_carrier_override(carrier)

    # 1. Classic binary struct — the payload carrier name lives here.
    classic_bytes = bytes(sb.setter.get_data())
    print(f"[classic] statusBarOverrides: {len(classic_bytes)} bytes, "
          f"carrier={sb.get_carrier_override()!r}")

    # 2. FeatureFlags plist — disable BOTH Speakeasy gates so the legacy
    #    status bar (and its classic file) is used. Run 5 armed
    #    SpeakeasyNewStatusBar enabled, so it must be disabled again here.
    flags = {
        "SpringBoard": {
            "Speakeasy": {"Enabled": False},
            "SpeakeasyNewStatusBar": {"Enabled": False},
        },
    }
    print("[flags] Speakeasy=OFF, SpeakeasyNewStatusBar=OFF")

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
    ]

    print("\n[start] three-phase protective backup path:")
    final_alert = await dm.start_restore(
        files, use_bookrestore=False,
        update_label=lambda x: print("   ", x))
    print("RESULT:", final_alert.txt if final_alert else None)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
