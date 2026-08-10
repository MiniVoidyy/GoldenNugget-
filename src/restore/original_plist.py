"""Original plist capture, templating, and materialization.

On a freshly restored (or clean) device, Nugget can back up the original
system plists it later overwrites. Device-specific values (model, serial,
device name, ...) are replaced with ``<Placeholder>`` keys so the templates
are shareable across any device of the same model + iOS build. When resetting
(or applying) tweaks, the placeholders are substituted back with the *current*
device's values, restoring the user's original settings instead of writing an
empty plist (which is what caused boot loops).

Capture uses the same selective mobilebackup2 mechanism as the protective
backup: files the device uploads are filtered mid-stream so only the plists we
care about (plus the backup metadata) are written to disk. The on-device
Manifest.db is then used to map ``(domain, relativePath)`` back to the
payload files.
"""

import plistlib
import sqlite3
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service

from src.exceptions.nugget_exception import NuggetException

# Keys from lockdown ``all_values`` whose string values are device-specific
# and should be replaced with placeholders when templating.
_TEMPLATE_KEYS = (
    "ProductType",
    "HardwareModel",
    "HardwarePlatform",
    "ProductVersion",
    "BuildVersion",
    "DeviceName",
    "SerialNumber",
    "UniqueDeviceID",
    "RegionInfo",
    "BasebandRegionSKU",
    "DeviceClass",
    "ProductName",
    "CPUArchitecture",
    "WiFiAddress",
    "BluetoothAddress",
    "MLBSerialNumber",
    "DieID",
    "FirmwareVersion",
    "PartitionType",
)

# Absolute path prefix -> backup (domain prefix, remainder handling).
# Mirrors the mapping in DeviceManager.get_domain_for_path, but always uses
# the fully-patched domain names (independent of the sparserestore status).
_BACKUP_DOMAIN_MAPPINGS = (
    ("/var/Managed Preferences/", "ManagedPreferencesDomain", False),
    ("/var/root/", "RootDomain", False),
    ("/var/preferences/", "SystemPreferencesDomain", False),
    ("/var/MobileDevice/", "MobileDeviceDomain", False),
    ("/var/mobile/", "HomeDomain", False),
    ("/var/db/", "DatabaseDomain", False),
    ("/var/containers/Shared/SystemGroup/", "SysSharedContainerDomain-", True),
    ("/var/containers/Data/SystemGroup/", "SysContainerDomain-", True),
)


def absolute_path_to_backup_location(path: str) -> tuple[Optional[str], Optional[str]]:
    """Map an absolute device path to ``(domain, relativePath)`` as used in Manifest.db."""
    for prefix, domain, is_container in _BACKUP_DOMAIN_MAPPINGS:
        if path.startswith(prefix):
            rest = path[len(prefix):]
            if is_container:
                group, sep, rel = rest.partition("/")
                if not sep:
                    return domain + group, ""
                return domain + group, rel
            return domain, rest
    return None, None


def get_device_values(all_values: dict) -> dict[str, str]:
    """Extract the templatable device-specific values from lockdown values."""
    values = {}
    for key in _TEMPLATE_KEYS:
        value = all_values.get(key)
        if isinstance(value, str) and value:
            values[key] = value
    return values


def _walk(obj, transform):
    if isinstance(obj, dict):
        return {k: _walk(v, transform) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(v, transform) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, transform) for v in obj)
    return transform(obj)


def template_plist(plist, device_values: dict[str, str]):
    """Replace device-specific string values with ``<Key>`` placeholders."""
    inverse = {}
    for key, value in device_values.items():
        if len(value) >= 5 and value not in inverse:
            inverse[value] = key

    def transform(value):
        if isinstance(value, str) and value in inverse:
            return f"<{inverse[value]}>"
        return value

    return _walk(plist, transform)


def materialize_plist(plist, device_values: dict[str, str]):
    """Substitute ``<Key>`` placeholders back with the current device's values."""
    def transform(value):
        if (isinstance(value, str) and value.startswith("<") and value.endswith(">")
                and len(value) > 2):
            key = value[1:-1]
            replacement = device_values.get(key)
            if replacement:
                return replacement
        return value

    return _walk(plist, transform)


async def capture_original_plists(
    udid: str,
    paths: list[str],
    update_label=lambda x: None,
    update_progress=lambda x: None,
) -> dict[str, bytes]:
    """Capture and template the given absolute plist paths from the device.

    Returns a dict of ``absolute_path -> templated bytes`` for the files that
    exist on the device and parse as plists.

    The capture runs a full mobilebackup2 backup (a filtered backup makes the
    device abort with ``Manifest references files not in backup``), then reads
    the wanted payloads straight from the on-device Manifest.db. The backup is
    kept in a temporary directory that is removed when done.
    """
    update_label("Backing up device to capture original plists...")
    ld = await create_using_usbmux(serial=udid)
    try:
        with TemporaryDirectory() as tmp_dir:
            async with Mobilebackup2Service(ld) as backup_client:
                await backup_client.backup(
                    full=True,
                    backup_directory=tmp_dir,
                    progress_callback=update_progress,
                )
            return _read_originals(Path(tmp_dir) / udid, paths)
    finally:
        try:
            await ld.close()
        except Exception:
            pass


def _read_originals(device_dir: Path, paths: list[str]) -> dict[str, bytes]:
    manifest = device_dir / "Manifest.db"
    if not manifest.exists():
        raise NuggetException("Could not find the backup manifest (Manifest.db).")
    conn = sqlite3.connect(str(manifest))
    try:
        rows = conn.execute("SELECT fileID, domain, relativePath FROM Files").fetchall()
    finally:
        conn.close()
    lookup = {(domain, rel): file_id for file_id, domain, rel in rows}

    result = {}
    for path in paths:
        domain, rel = absolute_path_to_backup_location(path)
        if domain is None:
            continue
        file_id = lookup.get((domain, rel))
        if not file_id:
            continue
        payload = device_dir / file_id[:2] / file_id
        if not payload.exists():
            continue
        data = payload.read_bytes()
        try:
            plistlib.loads(data)
        except Exception:
            print(f"Skipping non-plist original: {path}")
            continue
        result[path] = data
    return result
