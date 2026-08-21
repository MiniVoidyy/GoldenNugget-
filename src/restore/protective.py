"""
Protective backup module for iOS 27+.

On iOS 27, the sparse restore triggers a "safe state recovery" that purges
device data not present in the backup (photos, Apple ID credentials, user
settings). To keep user data alive, the three-phase flow in restore.py does:

  Phase 1 (this module): selective device backup. App containers are skipped
      device-side (empty Applications dict in the factory info), and every
      non-protective file the device uploads is discarded mid-stream instead
      of being written to disk. Peak disk usage drops from a full backup
      (10-100+ GB) to just the protective payload. If the selective upload
      fails for any reason, we automatically fall back to a full backup.
  Phase 3 (this module): the same backup directory — with Manifest.db pruned
      to the protective rows and orphan payload files removed — is restored
      back to the device after the security recovery.

Protective scope: HomeDomain/{Accounts, ConfigurationProfiles, Preferences,
Library/SpringBoard} (Apple ID + user settings + home screen layout),
Library/ControlCenter (Control Center module layout), and, optionally,
CameraRollDomain + MediaDomain (photos). KeychainDomain is
intentionally excluded: enabling backup encryption is slow and keychain data
is not needed for tweak functionality.
"""

import asyncio
import hashlib
import os
import plistlib
import shutil
import sqlite3
import struct
import time
import uuid as _uuid
import warnings
from collections.abc import Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Optional, cast

import pymobiledevice3.exceptions as _pm3_exc
import pymobiledevice3.service_connection as _sc
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service

from PySide6.QtCore import QCoreApplication

from src.exceptions.nugget_exception import NuggetException


# Minimum free disk space required before any device backup is started.
# Backups (protective, psysbackup, PosterBoard) are written to the system
# temp directory and can easily reach several GB (photos, app data). Overridable
# via the GOLDENNUGGET_MIN_FREE_GB environment variable.
MIN_FREE_DISK_GB = 5.0


def _min_free_disk_bytes() -> int:
    try:
        return int(float(os.environ.get("GOLDENNUGGET_MIN_FREE_GB", str(MIN_FREE_DISK_GB))) * (1024 ** 3))
    except ValueError:
        return int(MIN_FREE_DISK_GB * (1024 ** 3))


def check_disk_space(path: str = None, min_free_bytes: int = None) -> None:
    """Raise ``NuggetException`` if free disk space is below the backup threshold.

    Device backups are written to disk (temp directory by default); a full
    backup can be tens of GB. Fail early with a clear error instead of filling
    the disk mid-backup, which would corrupt the backup and the apply flow.
    """
    import tempfile
    if path is None:
        path = tempfile.gettempdir()
    if min_free_bytes is None:
        min_free_bytes = _min_free_disk_bytes()
    usage = shutil.disk_usage(path)
    if usage.free < min_free_bytes:
        free_gb = usage.free / (1024 ** 3)
        required_gb = min_free_bytes / (1024 ** 3)
        raise NuggetException(
            QCoreApplication.translate(
                "Nugget",
                "Not enough free disk space: only {0} GB available, at least {1} GB is required for the backup. "
                "Free up space on your computer (backups are written to {2}) and try again.",
            ).format(f"{free_gb:.1f}", f"{required_gb:.1f}", path)
        )
    return usage


async def _get_device_used_storage(lockdown_client) -> Optional[int]:
    """Return the device's used data storage in bytes, or ``None`` if unreadable.

    Queries the diagnostics relay's ``All`` report. ``TotalDataCapacity`` is the
    total size of the data partition and ``TotalDataSpace`` is its free space, so
    the difference is how much data a full device backup would carry. A full
    backup mirrors roughly the used capacity, so this is the disk space a backup
    needs to be written to the computer without exhausting it.
    """
    try:
        from pymobiledevice3.services.diagnostics import DiagnosticsService
        async with DiagnosticsService(lockdown_client) as diag:
            report = await diag.info("All")
        if not isinstance(report, dict):
            return None
        capacity = report.get("TotalDataCapacity")
        free = report.get("TotalDataSpace")
        if capacity is None or free is None:
            nested = report.get("DiskUsage")
            if isinstance(nested, dict):
                capacity = nested.get("TotalDataCapacity", capacity)
                free = nested.get("TotalDataSpace", free)
        if capacity is None or free is None:
            return None
        used = int(capacity) - int(free)
        return used if used > 0 else None
    except Exception:
        return None


async def check_disk_space_for_backup(lockdown_client=None, path: str = None,
                                      min_free_bytes: int = None) -> int:
    """Check free disk space before a device backup, sized to the device's data.

    The required free space is derived from the amount of data actually stored
    on the device (a full backup mirrors used capacity), never below the
    ``MIN_FREE_DISK_GB`` floor. If the device cannot be queried, the floor is
    used. Returns the required free space in bytes that was enforced.
    """
    if min_free_bytes is None:
        min_free_bytes = _min_free_disk_bytes()
        if lockdown_client is not None:
            used = await _get_device_used_storage(lockdown_client)
            if used is not None:
                min_free_bytes = max(min_free_bytes, used)
    check_disk_space(path=path, min_free_bytes=min_free_bytes)
    return min_free_bytes

# Bump SSL handshake timeout — the default 10 seconds is too short for
# mobilebackup2 service startup on busy or post-reboot devices (iOS 27+).
# Importing this module applies it process-wide.
_sc.DEFAULT_SSL_HANDSHAKE_TIMEOUT = 60

# Log file path
_LOG_FILE = "/tmp/goldennugget_log.txt"

def _log_write(msg: str) -> None:
    """Write message to log file (always writes, regardless of debug mode)."""
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass  # Never fail on logging

def log_info(msg: str) -> None:
    """Log info message (always writes to log file)."""
    print(f"[INFO] {msg}")
    _log_write(f"[INFO] {msg}")

def log_warn(msg: str) -> None:
    """Log warning message (always writes to log file)."""
    print(f"[WARN] {msg}")
    _log_write(f"[WARN] {msg}")

def log_error(msg: str) -> None:
    """Log error message (always writes to log file)."""
    print(f"[ERROR] {msg}")
    _log_write(f"[ERROR] {msg}")

# --- DeviceLink protocol constants (from pymobiledevice3.services.device_link) ---
_SIZE_FORMAT = ">I"
_CODE_FORMAT = ">B"
_CODE_FILE_DATA = 0xC
_CODE_ERROR_REMOTE = 0xB
_CODE_SUCCESS = 0

# Backup metadata files that must always be preserved (never filtered out)
_BACKUP_METADATA_FILES = frozenset({
    "Manifest.db",
    "Manifest.plist",
    "Status.plist",
    "Info.plist",
    "backup_manifest.db",
})

# Domains whose files should be kept in the protective backup.
PROTECTIVE_DOMAINS = frozenset({
    "CameraRollDomain",  # Actual photos and videos (DCIM/)
    "MediaDomain",       # Photo metadata (PhotoData/), PhotoStream, other media
})

# Path prefixes within HomeDomain that contain Apple ID account data and
# user settings.
APPLE_ID_PATH_PREFIXES = (
    "Library/Accounts",              # Account database (Accounts3.sqlite)
    "Library/ConfigurationProfiles",  # Configuration profiles
    "Library/Preferences",           # User settings (dark mode, wallpaper, etc.)
)

# NOTE: ConfigurationProfiles backup/restore was added in commit 25006f5
# (Aug 12) to preserve MDM/VPN/WebClip profiles across the restore cycle,
# but this widened the Phase 3 restore scope enough to also roll back
# applied tweaks on repeat apply and corrupt the PosterBoard database.
# Profiles are not reliably preserved by this approach anyway (confirmed
# still reset in practice), so scope is reverted to the narrow pre-fix
# state. If profile preservation is revisited, it needs a separate,
# isolated restore path that does not share scope with tweak/PosterBoard
# state — see regression found in 8.3 (reverted before public release).

# Path prefixes within HomeDomain that hold SpringBoard's home screen layout
# and icon state. Restoring these keeps the home screen (icon layout, folders,
# dock) intact after the iOS 27 "safe state recovery" wipe.
SPRINGBOARD_PATH_PREFIXES = (
    "Library/SpringBoard",
)

# Path prefixes within HomeDomain holding the Control Center module layout
# (Library/ControlCenter/ModuleConfiguration.plist). Not part of the
# "user settings" prefix above, so it must be listed explicitly — otherwise
# the iOS 27 wipe resets Control Center to its default modules.
CONTROL_CENTER_PATH_PREFIXES = (
    "Library/ControlCenter",
)

# Files/dirs inside the protective HomeDomain scope that tweaks write
# themselves — restoring the stale copies would undo the applied tweaks.
_SKIP_PATH_PREFIXES = (
    "Library/SpringBoard/statusBarOverrides",  # Not captured stale; re-injected with fresh tweak content
)

# Files iOS manages internally and rejects if included in a sparse backup
# with incorrect metadata (e.g. wrong protection class). With copy=True the
# existing on-device data is preserved anyway, so skipping them is safe.
_SKIP_FILES = frozenset({
    "keychain-backup.plist",    # iOS validates protection class, rejects flags=4
    ".GlobalPreferences.plist",  # Written separately as tweaks; skip to avoid overwrite
})


def _is_protective_file(domain: str, relative_path: str, include_photos: bool = True) -> bool:
    """Check if a file belongs in the protective backup."""
    filename = relative_path.rsplit("/", 1)[-1]
    if filename in _SKIP_FILES:
        return False
    if domain == "HomeDomain":
        if relative_path.startswith(_SKIP_PATH_PREFIXES):
            return False
        return (relative_path.startswith(APPLE_ID_PATH_PREFIXES)
                or relative_path.startswith(SPRINGBOARD_PATH_PREFIXES)
                or relative_path.startswith(CONTROL_CENTER_PATH_PREFIXES))
    if include_photos and domain in PROTECTIVE_DOMAINS:
        return True
    return False


class _SelectiveDeviceLink:
    """DeviceLink wrapper that discards non-protective files mid-stream.

    During backup the device sends every file via DLMessageUploadFiles.
    When ``preserve_file`` returns False for a file, its data is read off
    the socket and thrown away — no placeholder is created (an empty file's
    SHA1 never matches the Manifest.db digest, and clean_backup_for_restore
    removes the dangling Manifest rows before the backup is restored).

    All other DeviceLink operations delegate to the wrapped instance.
    """

    def __init__(self, device_link, preserve_file: Callable[[str, str], bool]):
        self._dl = device_link
        self._preserve_file = preserve_file

    def __getattr__(self, name):
        return getattr(self._dl, name)

    async def _recv_chunk_header(self) -> tuple:
        (size,) = struct.unpack(
            _SIZE_FORMAT, await self._dl.service.recvall(struct.calcsize(_SIZE_FORMAT)))
        (code,) = struct.unpack(
            _CODE_FORMAT, await self._dl.service.recvall(struct.calcsize(_CODE_FORMAT)))
        return size - struct.calcsize(_CODE_FORMAT), code

    async def upload_files(self, _message):
        while True:
            device_name = await self._dl._prefixed_recv()
            if not device_name:
                break
            file_name = await self._dl._prefixed_recv()
            size, code = await self._recv_chunk_header()

            if self._preserve_file(file_name, device_name):
                dest = self._dl.root_path / file_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as fd:
                    while size and code == _CODE_FILE_DATA:
                        fd.write(await self._dl.service.recvall(size))
                        size, code = await self._recv_chunk_header()
            else:
                # Discard incoming data — do NOT create an empty placeholder.
                while size and code == _CODE_FILE_DATA:
                    await self._dl.service.recvall(size)
                    size, code = await self._recv_chunk_header()

            if code == _CODE_ERROR_REMOTE:
                error_message = (await self._dl.service.recvall(size)).decode()
                warnings.warn(
                    f"Failed to fully upload: {file_name}. "
                    f"Device file name: {device_name}. Reason: {error_message}",
                    stacklevel=2,
                )
                continue
            assert code == _CODE_SUCCESS
        await self._dl.status_response(0)

    async def move_items(self, message):
        items = cast(Mapping[str, str], message[1])
        for src, dst in items.items():
            source = self._dl.root_path / src
            if not source.exists():
                # File was discarded during upload — nothing to move.
                continue
            dest = self._dl.root_path / dst
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source, dest)
        await self._dl.status_response(0)

    async def copy_item(self, message):
        # DLMessageCopyItem carries (src, dst) as positional message fields.
        # If the source was discarded during upload, skip instead of failing.
        src, dst = message[1], message[2]
        source = self._dl.root_path / src
        if source.exists():
            dest = self._dl.root_path / dst
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        await self._dl.status_response(0)


class ProtectiveBackupService(Mobilebackup2Service):
    """Mobilebackup2Service tuned for fast protective backups.

    - ``init_mobile_backup_factory_info`` returns an empty ``Applications``
      dict, so the device skips all app containers (AppDomain-*) entirely —
      they are never uploaded at all.
    - When ``preserve_file`` is provided, the DeviceLink upload/move/copy
      handlers are replaced with selective versions that discard
      non-protective file data mid-stream.
    - ``connect`` retries transient failures with exponential backoff —
      iOS 27+ devices can take a while to spin up mobilebackup2.
    """

    def __init__(self, lockdown, preserve_file: Optional[Callable[[str, str], bool]] = None):
        super().__init__(lockdown)
        self._preserve_file = preserve_file

    async def connect(self, max_retries: int = 5):
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                return await super().connect()
            except (_pm3_exc.ConnectionTerminatedError, ConnectionError,
                    OSError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt >= max_retries:
                    break
                delay = min(2 ** attempt, 15)
                print(
                    f"[ProtectiveBackup] mobilebackup2 connect failed "
                    f"(attempt {attempt}/{max_retries}), retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    async def init_mobile_backup_factory_info(self, afc):
        root_node = self.lockdown.all_values
        return {
            "iTunes Version": "10.0.1",
            "iTunes Files": {},
            "Unique Identifier": self.lockdown.udid.upper(),
            "Target Type": "Device",
            "Target Identifier": root_node["UniqueDeviceID"],
            "Serial Number": root_node["SerialNumber"],
            "Product Version": root_node["ProductVersion"],
            "Product Type": root_node["ProductType"],
            "Installed Applications": [],
            "GUID": _uuid.uuid4().bytes,
            "Display Name": root_node.get("DeviceName", ""),
            "Device Name": root_node.get("DeviceName", ""),
            "Build Version": root_node["BuildVersion"],
            "Applications": {},  # skip all app containers — big speedup
        }

    @asynccontextmanager
    async def device_link(self, backup_directory, **kwargs):
        from pymobiledevice3.services.device_link import DeviceLink
        dl = DeviceLink(self.service, Path(backup_directory))
        await dl.version_exchange()
        await self.version_exchange(dl)
        if self._preserve_file is not None:
            selective = _SelectiveDeviceLink(dl, preserve_file=self._preserve_file)
            handlers = getattr(dl, "_dl_handlers", {})
            # dl_loop dispatches via self._dl_handlers[command](message);
            # swap in the selective handlers where they exist.
            if "DLMessageUploadFiles" in handlers:
                handlers["DLMessageUploadFiles"] = selective.upload_files
            if "DLMessageMoveItems" in handlers:
                handlers["DLMessageMoveItems"] = selective.move_items
            if "DLMessageCopyItem" in handlers:
                handlers["DLMessageCopyItem"] = selective.copy_item
        try:
            yield dl
        finally:
            await dl.disconnect()


async def perform_protective_backup(
    lockdown_client: LockdownClient,
    backup_root: str,
    progress_callback=None,
    include_photos: bool = True,
) -> bool:
    """Run a selective device backup into ``backup_root``.

    Only protective data (photos, Apple ID, user settings) and the backup
    metadata are written to disk; everything else is discarded mid-stream.
    If the selective upload fails, automatically retries once as a full
    (unfiltered) backup so the flow never dies on a filtering edge case.

    Returns True if the device backup is encrypted.
    """
    if progress_callback is None:
        progress_callback = lambda x: None

    from src.exceptions.device_errors import is_device_locked_error as _is_device_locked_error
    from src.exceptions.device_errors import is_connection_error as _is_connection_error

    is_encrypted = False

    await check_disk_space_for_backup(lockdown_client, path=backup_root)

    shutil.rmtree(backup_root, ignore_errors=True)
    Path(backup_root).mkdir(parents=True, exist_ok=True)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            async with ProtectiveBackupService(lockdown_client) as mb:
                # Check if encryption is already enabled (don't enable it ourselves)
                try:
                    is_encrypted = await mb.get_will_encrypt()
                except Exception:
                    pass  # Non-fatal — encryption state only feeds the status label.

                if is_encrypted:
                    log_info("Backup encryption already enabled on device. Using existing encryption.")
                    progress_callback("Using existing backup encryption...")
                else:
                    log_info("Backup encryption not enabled — local manifest pruning will be used.")
                    progress_callback("Creating protective backup (unencrypted)...")

                try:
                    await mb.backup(full=True, backup_directory=backup_root,
                                    progress_callback=progress_callback)
                    break  # Success
                except Exception as e:
                    if _is_device_locked_error(e):
                        log_error("Protective backup failed: Device is locked. Please unlock your device and try again.")
                        raise NuggetException("Device is locked. Please unlock your device (enter passcode, be on home screen) and try again.")
                    if _is_connection_error(e) and attempt < max_retries:
                        delay = min(2 ** attempt, 15)
                        log_warn(f"Connection error during backup (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}")
                        progress_callback(f"Connection lost, retrying in {delay}s... (attempt {attempt}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    raise
        except Exception as e:
            if _is_device_locked_error(e):
                raise
            if _is_connection_error(e) and attempt < max_retries:
                continue
            raise

    return is_encrypted


def _iter_payload_files(device_dir: Path):
    """Yield every payload file in the backup, flat or in hash subdirectories."""
    for entry in sorted(device_dir.iterdir()):
        if entry.is_file():
            if entry.name not in _BACKUP_METADATA_FILES:
                yield entry
        elif entry.is_dir():
            yield from _iter_payload_files(entry)


def _is_encrypted_backup(device_dir: Path) -> bool:
    """Check if a backup directory has an encrypted Manifest.db."""
    try:
        from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
        return Mobilebackup2Service._is_encrypted_backup(device_dir)
    except Exception:
        return False


def _validate_sqlite_db(db_path: Path) -> bool:
    """Check if a file is a valid SQLite database."""
    if not db_path.exists() or db_path.stat().st_size < 100:
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        conn.close()
        return True
    except sqlite3.DatabaseError:
        return False


def clean_backup_for_restore(backup_dir: "str | Path", udid: str,
                              include_photos: bool = True) -> tuple:
    """Prune a backup directory down to its protective payload.

    1. Deletes every non-protective row from Manifest.db in a single DELETE
       (keep-set staged in a temp table instead of per-row DELETEs).
    2. Deletes payload files not referenced by the keep-set, scanning hash
       subdirectories too (iOS may store payloads as "<aa>/<fileID>").
    3. Removes directories left empty by the pruning.

    Returns (removed_manifest_rows, removed_payload_files).
    """
    device_dir = Path(backup_dir) / udid
    if not device_dir.is_dir():
        # Tolerate backup_dir already pointing at the device directory.
        if (Path(backup_dir) / "Manifest.db").exists():
            device_dir = Path(backup_dir)
        else:
            return 0, 0

    manifest_db = device_dir / "Manifest.db"
    if not manifest_db.exists():
        return 0, 0

    # If backup is encrypted, we can't read the manifest locally to prune it.
    # The device can restore encrypted backups directly, so skip local pruning.
    if _is_encrypted_backup(device_dir):
        log_info("Backup is encrypted — skipping local manifest pruning (device will handle it)")
        return 0, 0

    if not _validate_sqlite_db(manifest_db):
        log_error(f"Manifest.db at {manifest_db} is not a valid SQLite database. Skipping cleanup.")
        return 0, 0

    keep_ids = set()
    removed_rows = 0
    conn = sqlite3.connect(str(manifest_db))
    try:
        cur = conn.cursor()
        cur.execute("SELECT fileID, domain, relativePath FROM Files")
        for file_id, domain, rel_path in cur:
            if domain and rel_path and (_is_protective_file(domain, rel_path, include_photos)
                                        or domain == "SystemPreferencesDomain"):
                keep_ids.add(file_id)
            elif domain == "SystemPreferencesDomain" and rel_path == "":
                # the domain root directory row — without it the restore
                # agent may skip the whole domain
                keep_ids.add(file_id)

        cur.execute("CREATE TEMP TABLE nugget_keep (fileID TEXT PRIMARY KEY)")
        cur.executemany("INSERT INTO nugget_keep (fileID) VALUES (?)",
                        ((fid,) for fid in keep_ids))
        cur.execute("DELETE FROM Files WHERE fileID NOT IN (SELECT fileID FROM nugget_keep)")
        removed_rows = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        conn.commit()
    finally:
        conn.close()

    removed_files = 0
    for payload in _iter_payload_files(device_dir):
        if payload.name not in keep_ids:
            payload.unlink(missing_ok=True)
            removed_files += 1

    # Remove directories left empty (deepest first).
    for dirpath, _dirnames, _filenames in os.walk(device_dir, topdown=False):
        d = Path(dirpath)
        if d != device_dir and not any(d.iterdir()):
            d.rmdir()

    return removed_rows, removed_files


def _build_mbfile_blob(relative_path: str, contents: bytes, mode: int = 33188,
                       owner: int = 501, group: int = 501) -> bytes:
    """Build a ``MBFile`` archive blob for an injected backup file.

    Matches the NSKeyedArchiver structure BackupAgent2 writes to the
    ``file`` column of Manifest.db: an ``MBFile`` object carrying the file's
    metadata plus a ``Digest`` (SHA1 of the payload) and the data-protection
    extended attribute. Mode/ownership mirror a regular mobile-owned
    HomeDomain file; the extended attribute marks the file as exempt from
    data protection by SpringBoard (same as IconState.plist and friends).
    """
    now = int(time.time())
    extended_attributes = plistlib.dumps(
        {"com.apple.dataprotection.policy.exception-applied-by": b"com.apple.springboard"},
        fmt=plistlib.FMT_BINARY,
    )
    objects = [
        "$null",
        {
            "Birth": now,
            "LastModified": now,
            "LastStatusChange": now,
            "Flags": 0,
            "GroupID": group,
            "UserID": owner,
            "Mode": mode,
            "ProtectionClass": 4,
            "Size": len(contents),
            "RelativePath": plistlib.UID(2),
            "Digest": plistlib.UID(3),
            "ExtendedAttributes": plistlib.UID(4),
            "$class": plistlib.UID(5),
        },
        relative_path,
        hashlib.sha1(contents).digest(),
        extended_attributes,
        {"$classname": "MBFile", "$classes": ["MBFile", "NSObject"]},
    ]
    return plistlib.dumps(
        {
            "$version": 100000,
            "$archiver": "NSKeyedArchiver",
            "$top": {"root": plistlib.UID(1)},
            "$objects": objects,
        },
        fmt=plistlib.FMT_BINARY,
    )


def _patch_donor_blob(donor_blob: bytes, relative_path: str, contents: bytes,
                      mode: Optional[int] = None, owner: Optional[int] = None,
                      group: Optional[int] = None) -> bytes:
    """Re-target a real MBFile blob from the same backup for a new payload.

    Cloning a row the device itself produced guarantees byte-exact metadata
    (extended attributes, protection class) instead of risking a hand-built
    archive the restore agent might reject. Only the path, digest, size and
    (optionally) mode/ownership change.
    """
    blob = plistlib.loads(donor_blob)
    objects = blob["$objects"]
    info = objects[1]
    objects[info["RelativePath"]] = relative_path
    objects[info["Digest"]] = hashlib.sha1(contents).digest()
    info["Size"] = len(contents)
    if mode is not None:
        info["Mode"] = mode
    if owner is not None:
        info["UserID"] = owner
    if group is not None:
        info["GroupID"] = group
    return plistlib.dumps(blob, fmt=plistlib.FMT_BINARY)


def _pick_donor_blob(conn, domain: str, relative_path: str) -> "Optional[bytes]":
    """Pick a donor MBFile blob the restore agent will accept.

    The iOS 27 restore agent silently skips rows whose blob it considers
    invalid, and it deduplicates by inode. A safe donor is a regular (0644)
    file with a SpringBoard data-protection exception and a real inode:
    ``IconState.plist`` is the canonical such file in the protective scope.
    Falls back to any regular row carrying a digest, then to the old
    arbitrary-row behavior.
    """
    preferred = ("Library/SpringBoard/IconState.plist",)
    for candidate in preferred:
        row = conn.execute(
            "SELECT file FROM Files WHERE domain = ? AND relativePath = ? "
            "AND flags = 1 AND file IS NOT NULL",
            (domain, candidate),
        ).fetchone()
        if row is not None:
            return row[0]

    for candidate_flags, candidate_blob in conn.execute(
        "SELECT flags, file FROM Files WHERE domain = ? AND file IS NOT NULL "
        "AND relativePath != ? AND flags = 1",
        (domain, relative_path),
    ):
        try:
            info = plistlib.loads(candidate_blob)["$objects"][1]
            if (info.get("Mode", 0) & 0o777) == 0o644 and isinstance(
                info.get("InodeNumber"), int
            ):
                return candidate_blob
        except Exception:
            continue

    for candidate_flags, candidate_blob in conn.execute(
        "SELECT flags, file FROM Files WHERE domain = ? AND file IS NOT NULL "
        "AND relativePath != ? AND flags = 1",
        (domain, relative_path),
    ):
        try:
            info = plistlib.loads(candidate_blob)["$objects"][1]
            if "Digest" in info and "ExtendedAttributes" in info:
                return candidate_blob
        except Exception:
            continue
    return None


def _build_mbdir_blob(relative_path: str, mode: int = 16877) -> bytes:
    """Build an ``MBFile``-style archive blob for a directory row.

    Mirrors what BackupAgent2 writes for flag=2 rows (dump of the device's
    own SystemPreferencesDomain dir rows): no digest, size 0, S_IFDIR mode,
    root-owned. The device's real rows carry a real inode, so a unique one
    must be stamped by the caller.
    """
    now = int(time.time())
    objects = [
        "$null",
        {
            "Birth": now,
            "LastModified": now,
            "LastStatusChange": now,
            "Flags": 0,
            "GroupID": 0,
            "UserID": 0,
            "Mode": mode,
            "ProtectionClass": 4,
            "Size": 0,
            "RelativePath": plistlib.UID(2),
            "InodeNumber": 0,
            "$class": plistlib.UID(3),
        },
        relative_path,
        {"$classname": "MBFile", "$classes": ["MBFile", "NSObject"]},
    ]
    return plistlib.dumps(
        {
            "$version": 100000,
            "$archiver": "NSKeyedArchiver",
            "$top": {"root": plistlib.UID(1)},
            "$objects": objects,
        },
        fmt=plistlib.FMT_BINARY,
    )


def _ensure_directory_rows(conn, domain: str, relative_dir: str) -> None:
    """Insert flags=2 directory rows for every missing path component.

    The iOS 27 restore agent skips a file whose parent directories have no
    manifest rows, so before injecting a tweak file its directory chain must
    exist in Manifest.db. Rows are cloned from a real directory blob of the
    backup (byte-exact metadata) with a unique inode; falls back to a
    hand-built blob when the backup has no directory rows at all.
    """
    donor = conn.execute(
        "SELECT file FROM Files WHERE flags = 2 AND file IS NOT NULL LIMIT 1"
    ).fetchone()
    donor_blob = donor[0] if donor else None
    inode = _max_inode_in_manifest(conn)
    rel = ""
    for component in [""] + (relative_dir.split("/") if relative_dir else []):
        if component:
            rel = f"{rel}/{component}" if rel else component
        exists = conn.execute(
            "SELECT 1 FROM Files WHERE domain = ? AND relativePath = ? AND flags = 2",
            (domain, rel),
        ).fetchone()
        if exists:
            continue
        inode += 1
        if donor_blob is not None:
            blob = plistlib.loads(donor_blob)
            objects = blob["$objects"]
            info = objects[1]
            objects[info["RelativePath"]] = rel
        else:
            blob = plistlib.loads(_build_mbdir_blob(rel))
            objects = blob["$objects"]
        objects[1]["InodeNumber"] = inode
        blob = plistlib.dumps(blob, fmt=plistlib.FMT_BINARY)
        dir_id = hashlib.sha1(f"{domain}-{rel}".encode("utf-8")).hexdigest()
        conn.execute(
            "INSERT OR REPLACE INTO Files (fileID, domain, relativePath, flags, file) "
            "VALUES (?, ?, ?, ?, ?)",
            (dir_id, domain, rel, 2, sqlite3.Binary(blob)),
        )


def _max_inode_in_manifest(conn) -> int:
    """Largest inode claimed by any regular or directory row (0 when none has one)."""
    max_inode = 0
    for (candidate_blob,) in conn.execute(
        "SELECT file FROM Files WHERE flags IN (1, 2) AND file IS NOT NULL"
    ):
        try:
            ino = plistlib.loads(candidate_blob)["$objects"][1].get("InodeNumber")
            if isinstance(ino, int):
                max_inode = max(max_inode, ino)
        except Exception:
            continue
    return max_inode


def inject_file_into_backup(backup_dir: "str | Path", udid: str, domain: str,
                            relative_path: str, contents: bytes,
                            mode: Optional[int] = None,
                            owner: Optional[int] = None,
                            group: Optional[int] = None) -> bool:
    """Add a file to a pruned backup's Manifest.db and payload store.

    The iOS 27 "safe state recovery" wipe clears HomeDomain files that were
    staged by the sparse restore but are absent from the protective backup.
    Files the tweak writes can therefore be re-added here with their *new*
    content so Phase 3's mobilebackup2 restore lays them down natively (AFC
    cannot reach HomeDomain, so that is the only reliable path on iOS 27).

    The iOS 27 restore agent requires a well-formed regular-file blob with a
    real, *unique* inode (it deduplicates by inode — a clone sharing the
    donor's inode gets restored with the donor's content, and a fresh blob
    without an inode is skipped outright). The mode is normalized to a
    regular 0644-style file so the agent accepts the row.

    The file ID follows the standard ``SHA1("<domain>-<relativePath>")``
    convention and the payload is placed in the ``<aa>/<fileID>`` layout the
    restore agent expects. Returns True when the file was added.
    """
    device_dir = Path(backup_dir) / udid
    if not device_dir.is_dir():
        # Tolerate backup_dir already pointing at the device directory.
        if (Path(backup_dir) / "Manifest.db").exists():
            device_dir = Path(backup_dir)
        else:
            return False

    manifest_db = device_dir / "Manifest.db"
    if not manifest_db.exists():
        return False

    # If backup is encrypted, we can't inject files locally.
    # The tweaks will need to be applied after restore via AFC or other means.
    if _is_encrypted_backup(device_dir):
        log_warn(f"Backup is encrypted — skipping local file injection for {domain}/{relative_path}")
        return False

    if not _validate_sqlite_db(manifest_db):
        log_error(f"Manifest.db at {manifest_db} is not a valid SQLite database. Cannot inject file.")
        return False

    file_id = hashlib.sha1(f"{domain}-{relative_path}".encode("utf-8")).hexdigest()

    conn = sqlite3.connect(str(manifest_db))
    try:
        # The restore agent skips a file whose parent directory rows are
        # missing, so ensure the whole directory chain first.
        dir_path, _ = os.path.split(relative_path)
        _ensure_directory_rows(conn, domain, dir_path)

        # The restore agent validates the blob and deduplicates by inode:
        # pick a donor the agent accepts, then stamp a unique inode so the
        # restored file cannot be confused with the donor's own file.
        flags, blob = 1, None
        donor = _pick_donor_blob(conn, domain, relative_path)
        unique_inode = _max_inode_in_manifest(conn) + 1
        safe_mode = (mode or 33188) & 0o100777
        if safe_mode & 0o777 == 0:
            safe_mode |= 0o644
        if donor is None:
            blob = _build_mbfile_blob(
                relative_path, contents,
                mode=safe_mode, owner=owner or 501, group=group or 501)
        else:
            blob = _patch_donor_blob(
                donor, relative_path, contents,
                mode=safe_mode, owner=owner or 501, group=group or 501)
        patched = plistlib.loads(blob)
        patched["$objects"][1]["InodeNumber"] = unique_inode
        blob = plistlib.dumps(patched, fmt=plistlib.FMT_BINARY)
        payload = device_dir / file_id[:2] / file_id
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_bytes(contents)
        conn.execute(
            "INSERT OR REPLACE INTO Files (fileID, domain, relativePath, flags, file) "
            "VALUES (?, ?, ?, ?, ?)",
            (file_id, domain, relative_path, flags, sqlite3.Binary(blob)),
        )
        conn.commit()
        return True
    finally:
        conn.close()
    return True
