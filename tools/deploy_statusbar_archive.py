#!/usr/bin/env python3
"""Push a StatusBarOverrides.archive straight to a connected device.

This is the on-device counterpart of ``tools/fetch_statusbar_archive.py``: it
runs the *exact* code path the GUI apply uses for iOS 27 -- ``StatusBarTweak``
collects the classic overrides, ``apply_ios27_tweak`` builds the archive and
stages a single HomeDomain file -- and then hands that file to the sparse
restore, so what lands on the phone is what an "Apply Tweaks" would deliver.

It deliberately does **not** run the three-phase restore: no protective backup,
no security-recovery wipe, no data restore. Only the one status-bar file is
sent, which makes it safe to iterate on the archive contents.

Verify with::

    python tools/fetch_statusbar_archive.py   # byte-compare what came back

The phone has to be unlocked, and Find My has to be off (mobilebackup2 refuses
otherwise). SpringBoard reads the archive at boot, so a reboot is needed before
the new value shows up in the status bar.

Run: python tools/deploy_statusbar_archive.py --carrier "Mango" --badge P --bars 3
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.devicemanagement.session import lockdown_session
from src.restore import backup, perform_restore
from src.restore.restore import concat_regular_file
from src.tweaks.status_bar.status_bar_tweak import StatusBarTweak


def staged_archive(carrier, badge, bars, secondary_carrier, secondary_badge, secondary_bars):
    """Return the archive the GUI would stage for these overrides."""
    tweak = StatusBarTweak()
    tweak.enabled = True

    # Feed the classic overrides through the same setters the page uses, so
    # this exercises the getter forwarding in apply_ios27_tweak too.
    if carrier:
        tweak.set_carrier_override(carrier)
    if secondary_carrier:
        tweak.set_secondary_carrier_override(secondary_carrier)
    if badge:
        tweak.set_primary_service_badge(badge)
    if secondary_badge:
        tweak.set_secondary_service_badge(secondary_badge)
    if bars is not None:
        tweak.set_gsm_signal_strength_bars(bars)
    if secondary_bars is not None:
        tweak.set_secondary_gsm_signal_strength_bars(secondary_bars)

    staged: list = []
    tweak.apply_ios27_tweak(staged)
    if len(staged) != 1:
        raise SystemExit(f"expected exactly one staged file, got {len(staged)}")
    return staged[0]


def to_sparse_backup(file):
    """Wrap the staged file in the domain/directory rows a sparse restore needs."""
    files: list = []
    concat_regular_file(file, files, "", "")
    return backup.Backup(files=files, apps=[], manifest_ios27=True)


async def deploy(udid, payload, reboot):
    async with lockdown_session(udid) as lockdown:
        version = lockdown.product_version
        print(f"device {udid} on iOS {version}")
        print(f"archive  {len(payload.contents)} bytes -> {payload.domain}{payload.restore_path}")
        await perform_restore(
            backup=to_sparse_backup(payload),
            reboot=reboot,
            lockdown_client=lockdown,
        )


def first_usb_udid():
    """First USB-connected device, matching tools/fetch_statusbar_archive.py."""
    from pymobiledevice3.usbmux import list_devices
    usb = [d for d in asyncio.run(list_devices()) if d.is_usb]
    return usb[0].serial if usb else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carrier", help="primary carrier name")
    ap.add_argument("--secondary-carrier", help="secondary carrier name")
    ap.add_argument("--badge", help="primary service badge (max 8 chars)")
    ap.add_argument("--secondary-badge", help="secondary service badge (max 8 chars)")
    ap.add_argument("--bars", type=int, help="primary signal bars (clamped 0-5)")
    ap.add_argument("--secondary-bars", type=int, help="secondary signal bars")
    ap.add_argument("--reset", action="store_true",
                    help="send the reset record (clears the carrier override)")
    ap.add_argument("--udid", help="target UDID (default: first connected device)")
    ap.add_argument("--reboot", action="store_true",
                    help="reboot the device afterwards so SpringBoard re-reads the file")
    args = ap.parse_args()

    if not any([args.carrier, args.secondary_carrier, args.reset]):
        ap.error("nothing to do: pass --carrier/--secondary-carrier or --reset")

    from src.restore.statusbar_fetch import dump_path
    udid = args.udid or first_usb_udid()
    if not udid:
        raise SystemExit("no device found over usbmux")
    print(f"device: {udid}")
    print(f"verify with: python tools/fetch_statusbar_archive.py  (-> {dump_path(udid)})")

    file = staged_archive(
        None if args.reset else args.carrier,
        args.badge,
        args.bars,
        None if args.reset else args.secondary_carrier,
        args.secondary_badge,
        args.secondary_bars,
    )

    try:
        asyncio.run(deploy(udid, file, args.reboot))
    except Exception as exc:  # noqa: BLE001 - surface the device's own message
        text = str(exc)
        if "Find My" in text:
            raise SystemExit(
                "the device refused the restore because Find My is on.\n"
                "Turn it off (Settings -> [your name] -> Find My) and retry."
            ) from exc
        raise
    print("restore finished -- reboot the device, then fetch it back to verify")


if __name__ == "__main__":
    main()