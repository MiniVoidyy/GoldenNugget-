import asyncio
import hashlib
import os
import plistlib
import shutil
import ssl
import tempfile
import time

from . import backup, perform_restore, reboot_device
from .mbdb import _FileMode
from .protective import (
    clean_backup_for_restore,
    inject_file_into_backup,
    perform_keychain_appleid_backup,
    perform_protective_backup,
)
from pymobiledevice3.lockdown import LockdownClient, create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
from pymobiledevice3.exceptions import ConnectionTerminatedError, PyMobileDevice3Exception

class FileToRestore:
    def __init__(self,
                 contents: str, restore_path: str, contents_path: str = None, domain: str = "",
                 owner: int = 501, group: int = 501, mode: _FileMode = None
                ):
        self.contents = contents
        self.contents_path = contents_path
        self.restore_path = restore_path
        self.domain = domain
        self.owner = owner
        self.group = group
        self.mode = mode

def concat_exploit_file(file: FileToRestore, files_list: list[FileToRestore], last_domain: str) -> str:
    base_path = ""
    # set it to work in the separate volumes (prevents a bootloop)
    if file.restore_path.startswith("/var/mobile/"):
        # required on iOS 17.0+ since /var/mobile is on a separate partition
        base_path = "/var/mobile/backup"
    elif file.restore_path.startswith("/private/var/mobile/"):
        base_path = "/private/var/mobile/backup"
    elif file.restore_path.startswith("/private/var/"):
        base_path = "/private/var/backup"
    # don't append the directory if it has already been added (restore will fail)
    path, name = os.path.split(file.restore_path)
    domain_path = f"SysContainerDomain-../../../../../../../..{base_path}{path}/"
    new_last_domain = last_domain
    if last_domain != domain_path:
        files_list.append(backup.Directory(
            "",
            f"{domain_path}",
            owner=file.owner,
            group=file.group
        ))
        new_last_domain = domain_path
    files_list.append(backup.ConcreteFile(
        "",
        f"{domain_path}{name}",
        owner=file.owner,
        group=file.group,
        contents=file.contents
    ))
    return new_last_domain

def concat_regular_file(file: FileToRestore, files_list: list[FileToRestore], last_domain: str, last_path: str):
    path, name = os.path.split(file.restore_path)
    paths = path.split("/")
    new_last_domain = last_domain
    # append the domain first
    if last_domain != file.domain:
        files_list.append(backup.Directory(
            "",
            file.domain,
            owner=file.owner,
            group=file.group
        ))
        last_path = ""
        new_last_domain = file.domain
    # append each part of the path if it is not already there
    full_path = ""
    mode = file.mode
    if mode == None:
        mode = backup.DEFAULT
    for path_item in paths:
        if full_path != "":
            full_path += "/"
        full_path += path_item
        if not last_path.startswith(full_path):
            files_list.append(backup.Directory(
                full_path,
                file.domain,
                owner=file.owner,
                group=file.group,
                mode=mode
            ))
            last_path = full_path
    # finally, append the file
    files_list.append(backup.ConcreteFile(
        f"{full_path}/{name}",
        file.domain,
        owner=file.owner,
        group=file.group,
        contents=file.contents,
        src_path=file.contents_path,
        mode=mode
    ))
    return new_last_domain, full_path

# merge all files that have duplicates and returns the list without duplicates
def merge_duplicates(original_files: list[FileToRestore]) -> list[FileToRestore]:
    no_dupe_files: list[FileToRestore] = []
    existing_locations: dict[str: int] = {}
    for file in original_files:
        if file.domain == None:
            file_loc = "-"
        else:
            file_loc = file.domain + '-'
        restore_path = file.restore_path
        if file.restore_path.startswith('/'):
            restore_path = restore_path.removeprefix('/')
        file_loc += restore_path
        if file_loc in existing_locations:
            if not restore_path.endswith('.plist'):
                print(f'cannot merge duplicate file, ignoring {file_loc}')
                continue
            # merge the data (plist files only)
            print(f'merging duplicate files for {file_loc}')
            initial_data = plistlib.loads(no_dupe_files[existing_locations[file_loc]].contents)
            added_data = plistlib.loads(file.contents)
            initial_data.update(added_data)
            no_dupe_files[existing_locations[file_loc]].contents = plistlib.dumps(initial_data)
            del initial_data, added_data
        else:
            # add it to the no dupes list
            no_dupe_files.append(file)
            existing_locations[file_loc] = len(no_dupe_files) - 1
    return no_dupe_files

def has_sparserestore_capability(lockdown_client: LockdownClient = None) -> bool:
    if lockdown_client is None:
        return True
    try:
        ver = lockdown_client.product_version.split(".")
        major = int(ver[0])
        minor = int(ver[1]) if len(ver) > 1 else 0
    except (ValueError, IndexError):
        return True
    if major != 18:
        return major < 18
    # there is no iOS 18.0.2 and 18.0.1 works with sparserestore, so no need to check the patch number
    return minor == 0


# --- iOS 27+ four-phase restore --------------------------------------------
#
# Progress is mapped into per-phase ranges so the GUI bar never jumps
# backwards:
#   Phase 1 (protective backup):        0-35
#   Phase 2 (sparse restore + reboot):  35-55
#   Phase 3 (reconnect + restore):      55-90
#   Phase 4 (encrypted keychain backup): 90-100
_PHASE_BACKUP_END = 35
_PHASE_TWEAK_END = 55
_PHASE_RESTORE_END = 90

# How long to wait for the device to come back after the iOS 27 security
# recovery before giving up. Apple logo → reboot → progress bar (like
# Erase All Contents) → full boot can take several minutes.
_RECONNECT_TIMEOUT = 20 * 60

# HomeDomain tweak files. They are injected into the protective backup after
# pruning (with the freshly-applied tweak content) so Phase 3's mobilebackup2
# restore writes them back after the wipe cleared the sparse restore's copy.
# AFC cannot reach HomeDomain on iOS 27 — ``com.apple.afc`` only exposes the
# media directory — so backup injection is the one reliable path.
_HOME_DOMAIN_TWEAK_PATHS = (
    "Library/SpringBoard/statusBarOverrides",  # Status Bar tweak
    # FeatureFlags user-level override candidates (iOS 27). The system-level
    # /var/preferences/FeatureFlags/Global.plist is on the restore agent's
    # sysprefs allowlist-blocklist: backups may only rewrite files the device
    # already knows (verified with a radios.plist marker probe). These user
    # paths ride the same proven HomeDomain injection.
    "Library/Preferences/com.apple.FeatureFlags.plist",  # CFPreferences suite
    "Library/FeatureFlags/Global.plist",
    "Library/FeatureFlags/Domain/SpringBoard.plist",
)

# SystemPreferencesDomain tweak files, re-injected for the same reason as the
# HomeDomain ones: the iOS 27 wipe clears whatever the sparse restore staged
# unless the protective backup carries it. /var/preferences is outside the
# protective scope, so tweak files landing there must be injected by hand.
_SYSTEM_PREFERENCES_TWEAK_PATHS = (
    "FeatureFlags/Global.plist",  # Status Bar (Speakeasy) feature flag override
)

# Run 7 (iOS 27): the Speakeasy gate in SpringBoard reads flag
# "Speakeasy"/"SpeakeasyNewStatusBar" of domain "SpringBoard" (confirmed in
# /System/Library/FeatureFlags/Domain/SpringBoard.plist of 24A5408d). The only
# override store FeatureFlags.framework reads is /var/preferences/FeatureFlags/
# Settings.plist, so every writable surface gets armed: the HomeDomain prefs
# plists (CFPreferences suites read by SpringBoard/UIKit at boot) plus a new
# SystemPreferencesDomain row aimed at the system store (delivery is verified
# via the post-restore backup).
_SPEAKEASY_DISABLE_FLAGS = (
    "Speakeasy",
    "SpeakeasyNewStatusBar",
    "SpeakeasyAttributionManager",
    "SpeakeasyStatusBarWindowRotation",
)
_SPEAKEASY_PREF_KEYS = {flag: False for flag in _SPEAKEASY_DISABLE_FLAGS}
_SPEAKEASY_FLAG_DICT = {flag: {"Enabled": False} for flag in _SPEAKEASY_DISABLE_FLAGS}
_SPEAKEASY_PLIST_PATHS = (
    "Library/Preferences/com.apple.springboard.plist",
    "Library/Preferences/com.apple.SpringBoard.plist",
    "Library/Preferences/com.apple.UIKit.plist",
    "Library/Preferences/com.apple.FeatureFlags.plist",
)
# MCX (MDM) managed preferences — read with higher priority than user
# defaults by CFPreferences, so they can force the gate's pref lookups off.
_SPEAKEASY_MANAGED_PLIST_PATHS = (
    "mobile/com.apple.springboard.plist",
    "mobile/com.apple.UIKit.plist",
    "mobile/com.apple.FeatureFlags.plist",
)
_SYSTEM_FF_SETTINGS_PATH = "FeatureFlags/Settings.plist"
_ROOT_DOMAIN_FF_PATHS = (
    "preferences/FeatureFlags/Settings.plist",
    "Library/FeatureFlags/Settings.plist",
)


def _read_manifest_plist(device_dir: str, domain: str, rel_path: str):
    """Load a plist the way the fresh backup stored it (payload <aa>/<fileID>)."""
    import sqlite3 as _sqlite3
    file_id = hashlib.sha1(f"{domain}-{rel_path}".encode("utf-8")).hexdigest()
    payload = os.path.join(device_dir, file_id[:2], file_id)
    conn = _sqlite3.connect(os.path.join(device_dir, "Manifest.db"))
    try:
        row = conn.execute(
            "SELECT file FROM Files WHERE fileID = ?", (file_id,)
        ).fetchone()
    finally:
        conn.close()
    data = None
    if os.path.exists(payload):
        data = open(payload, "rb").read()
    if data is None and row is not None and row[0] is not None:
        try:
            blob = plistlib.loads(row[0])
            if "Digest" in blob["$objects"][1]:
                digest = blob["$objects"][blob["$objects"][1]["Digest"]]
                data = bytes(digest)
        except Exception:
            data = None
    if data is None:
        return {}
    try:
        return plistlib.loads(data)
    except Exception:
        return {}


def _inject_speakeasy_disable(backup_root: str, udid: str) -> list:
    """Arm every writable Speakeasy-disable surface in the pruned backup."""
    device_dir = os.path.join(backup_root, udid)
    if not os.path.isdir(device_dir):
        device_dir = backup_root
    if not os.path.exists(os.path.join(device_dir, "Manifest.db")):
        return []
    injected = []
    for rel_path in _SPEAKEASY_PLIST_PATHS:
        plist = _read_manifest_plist(device_dir, "HomeDomain", rel_path)
        if rel_path.endswith("com.apple.FeatureFlags.plist"):
            category = plist.setdefault("SpringBoard", {})
            category.update(_SPEAKEASY_FLAG_DICT)
        else:
            plist.update(_SPEAKEASY_PREF_KEYS)
        ok = inject_file_into_backup(
            backup_root, udid, "HomeDomain", rel_path,
            plistlib.dumps(plist, fmt=plistlib.FMT_BINARY),
            mode=_FileMode.S_IFREG | 0o644,
        )
        injected.append((f"HomeDomain/{rel_path}", ok))
    for rel_path in _SPEAKEASY_MANAGED_PLIST_PATHS:
        plist = _read_manifest_plist(device_dir, "ManagedPreferencesDomain", rel_path)
        if rel_path.endswith("com.apple.FeatureFlags.plist"):
            category = plist.setdefault("SpringBoard", {})
            category.update(_SPEAKEASY_FLAG_DICT)
        else:
            plist.update(_SPEAKEASY_PREF_KEYS)
        ok = inject_file_into_backup(
            backup_root, udid, "ManagedPreferencesDomain", rel_path,
            plistlib.dumps(plist, fmt=plistlib.FMT_BINARY),
            mode=_FileMode.S_IFREG | 0o644,
        )
        injected.append((f"ManagedPreferencesDomain/{rel_path}", ok))
    settings = {"SpringBoard": dict(_SPEAKEASY_FLAG_DICT)}
    ok = inject_file_into_backup(
        backup_root, udid, "SystemPreferencesDomain", _SYSTEM_FF_SETTINGS_PATH,
        plistlib.dumps(settings, fmt=plistlib.FMT_BINARY),
        mode=_FileMode.S_IFREG | 0o644,
        owner=0, group=0,
    )
    injected.append((f"SystemPreferencesDomain/{_SYSTEM_FF_SETTINGS_PATH}", ok))
    for rel_path in _ROOT_DOMAIN_FF_PATHS:
        ok = inject_file_into_backup(
            backup_root, udid, "RootDomain", rel_path,
            plistlib.dumps(settings, fmt=plistlib.FMT_BINARY),
            mode=_FileMode.S_IFREG | 0o644,
            owner=0, group=0,
        )
        injected.append((f"RootDomain/{rel_path}", ok))
    return injected


def _scaled_callback(progress_callback, lo: float, hi: float):
    """Map pymobiledevice3's raw 0-100 progress into the [lo, hi] range.

    Status strings pass through untouched (the GUI shows them as labels);
    other non-numeric values are dropped so the bar never sees garbage.
    """
    span = hi - lo

    def _cb(value):
        if isinstance(value, str):
            progress_callback(value)
            return
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        pct = max(0.0, min(100.0, float(value)))
        progress_callback(lo + span * pct / 100.0)

    return _cb


async def _wait_for_device(udid: str, progress_callback,
                           timeout: float = _RECONNECT_TIMEOUT) -> LockdownClient:
    """Wait for the device to return after the iOS 27 security recovery.

    Polls usbmux with capped exponential backoff. Fully async — the caller's
    event loop (and the GUI) stays responsive for the whole wait.
    """
    from pymobiledevice3.exceptions import (
        DeviceNotFoundError, PasswordRequiredError, NotPairedError,
        ConnectionFailedError, ConnectionTerminatedError,
    )
    start = time.monotonic()
    deadline = start + timeout
    delay = 5.0
    last_error = None
    while True:
        elapsed = int(time.monotonic() - start)
        progress_callback(
            f"Waiting for device after security recovery "
            f"({elapsed // 60}:{elapsed % 60:02d} elapsed)..."
        )
        try:
            return await create_using_usbmux(serial=udid, autopair=True)
        except (DeviceNotFoundError, PasswordRequiredError, NotPairedError,
                ConnectionFailedError, ConnectionTerminatedError,
                ConnectionError, OSError,
                asyncio.TimeoutError) as e:
            last_error = e
        if time.monotonic() + delay > deadline:
            break
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, 30.0)
    raise DeviceNotFoundError(
        f"Device {udid} not reachable after reboot "
        f"({int(timeout // 60)} min timeout). Unlock the device and make "
        f"sure it is connected via USB. Last error: {last_error}"
    )


def _is_transient_restore_error(error) -> bool:
    """True for Phase 3 errors that mean 'device still booting, try again'."""
    name = type(error).__name__
    msg = str(error)
    # ssl.SSLError subclasses OSError, so this covers SSL drops too.
    if isinstance(error, (ConnectionTerminatedError, OSError)):
        return True
    if "InvalidService" in name:
        return True
    # MBErrorDomain/1: SpringBoard not ready for a restore yet.
    if "SpringBoard" in msg and "ready for a restore" in msg:
        return True
    return "start" in msg.lower() and "service" in msg.lower()


async def _restore_protective_backup(lc: LockdownClient, backup_root: str,
                                     udid: str, reboot: bool,
                                     progress_callback) -> None:
    """Phase 3: restore the pruned protective backup.

    Retries while SpringBoard / mobilebackup2 are still coming up after the
    security recovery (they can take minutes on iOS 27).

    The progress_callback is already pre-scaled by the caller.
    """
    max_retries = 12
    for attempt in range(1, max_retries + 1):
        try:
            async with Mobilebackup2Service(lc) as mb:
                await mb.restore(
                    backup_root,
                    system=True, copy=True, remove=False,
                    reboot=reboot, source=udid,
                    skip_apps=True,
                    progress_callback=progress_callback,
                )
            return
        except (PyMobileDevice3Exception, ConnectionTerminatedError,
                ssl.SSLError, OSError) as e:
            if attempt >= max_retries or not _is_transient_restore_error(e):
                raise
            progress_callback(
                f"Device not ready, retrying ({attempt}/{max_retries})..."
            )
            await asyncio.sleep(10)


async def _restore_ios27(back: backup.Backup, reboot: bool,
                         lockdown_client: LockdownClient, progress_callback):
    """iOS 27+ four-phase restore: backup → tweak → reboot → restore → keychain backup.

    Phase 1 (0-35%):  Selective backup of photos, Apple ID, and user
                      settings. Non-protective data is discarded mid-stream,
                      so no multi-GB full backup ever hits the disk.
                      (KeychainDomain is skipped — enabling backup
                      encryption is slow and not needed for tweaks.)
    Phase 2 (35-55%): Apply tweaks via sparse restore → reboot, which
                      triggers the iOS 27 "safe state recovery" wipe.
    Phase 3 (55-90%): Reconnect and restore the pruned Phase 1 backup so
                      user data survives the wipe.
    Phase 4 (90-100%): Encrypted backup of KeychainDomain + HomeDomain
                      (Apple ID accounts, ConfigurationProfiles, preferences).
                      This gives the user a complete encrypted backup they can
                      restore from if anything goes wrong. Requires device
                      passcode for encryption.
    """
    udid = lockdown_client.udid
    protective_dir = tempfile.mkdtemp(prefix="nugget_protective_")
    backup_root = os.path.join(protective_dir, "device_backup")
    os.makedirs(backup_root, exist_ok=True)
    backup_complete = False
    try:
        # === Phase 1: selective protective backup (0-35%) ===
        progress_callback(0)
        await perform_protective_backup(
            lockdown_client, backup_root,
            progress_callback=_scaled_callback(progress_callback, 0, _PHASE_BACKUP_END),
            include_photos=True,
        )
        backup_complete = True

        # Prune Manifest.db + orphan payloads in a worker thread — a full
        # manifest can have 100k+ rows, too heavy for the event loop.
        removed_rows, removed_files = await asyncio.to_thread(
            clean_backup_for_restore, backup_root, udid
        )
        print(f"[iOS27] Protective backup pruned: "
              f"-{removed_rows} manifest rows, -{removed_files} payload files")

        # Re-inject the HomeDomain tweak files into the pruned backup so Phase
        # 3 restores their *fresh* content. The wipe can drop the copy the
        # sparse restore (Phase 2) stages, and these paths are intentionally
        # excluded from the backup so a stale on-device copy never overwrites
        # the tweak — injecting the new content covers both cases. AFC cannot
        # reach HomeDomain on iOS 27, so this is the only reliable path.
        for file in back.files:
            if (isinstance(file, backup.ConcreteFile)
                    and file.domain == "HomeDomain"
                    and file.path in _HOME_DOMAIN_TWEAK_PATHS):
                inject_file_into_backup(
                    backup_root, udid, file.domain, file.path,
                    file.read_contents(),
                    mode=_FileMode.S_IFREG | 0o644,
                    owner=file.owner, group=file.group)
            elif (isinstance(file, backup.ConcreteFile)
                    and file.domain == "SystemPreferencesDomain"
                    and file.path in _SYSTEM_PREFERENCES_TWEAK_PATHS):
                ok = inject_file_into_backup(
                    backup_root, udid, file.domain, file.path,
                    file.read_contents(),
                    mode=_FileMode.S_IFREG | 0o644,
                    owner=file.owner, group=file.group)
                print(f"[iOS27] Injected {file.domain}/{file.path} "
                      f"into protective backup: {ok}")

        for label, ok in _inject_speakeasy_disable(backup_root, udid):
            print(f"[iOS27] Speakeasy-disable {label}: {ok}")

        progress_callback(_PHASE_BACKUP_END)

        # === Phase 2: apply tweaks → reboot (35-55%) ===
        try:
            await perform_restore(
                backup=back, reboot=True,
                lockdown_client=lockdown_client,
                progress_callback=_scaled_callback(
                    progress_callback, _PHASE_BACKUP_END, _PHASE_TWEAK_END),
            )
        except (ConnectionTerminatedError, ssl.SSLEOFError,
                ConnectionAbortedError, ConnectionResetError):
            # Device rebooted before acknowledging — expected.
            pass
        progress_callback(_PHASE_TWEAK_END)

        # === Phase 3: reconnect + restore protective backup (55-90%) ===
        lc = await _wait_for_device(udid, progress_callback)
        try:
            # SpringBoard may still be launching after a fresh boot; the
            # restore retry loop handles readiness, this just avoids an
            # instant first failure.
            progress_callback("Waiting for SpringBoard to finish launching...")
            await asyncio.sleep(10)
            await _restore_protective_backup(
                lc, backup_root, udid, reboot,
                _scaled_callback(progress_callback, _PHASE_TWEAK_END, _PHASE_RESTORE_END))
        finally:
            try:
                await lc.close()
            except Exception:
                # Connection may already be severed by the final reboot.
                pass

        # === Phase 4: encrypted keychain + Apple ID backup (90-100%) ===
        progress_callback(_PHASE_RESTORE_END)
        keychain_dir = os.path.join(protective_dir, "keychain_backup")
        os.makedirs(keychain_dir, exist_ok=True)
        try:
            # Reconnect for the keychain backup (Phase 3's connection is closed)
            lc4 = await _wait_for_device(udid, progress_callback, timeout=60)
            await perform_keychain_appleid_backup(
                lc4, keychain_dir,
                progress_callback=_scaled_callback(progress_callback, _PHASE_RESTORE_END, 100))
            await lc4.close()
            print(f"[iOS27] Phase 4 complete: encrypted keychain backup at {keychain_dir}")
        except Exception as e:
            # Phase 4 is best-effort — don't fail the whole restore if it fails.
            print(f"[iOS27] Phase 4 (keychain backup) failed: {e}")
            progress_callback("Keychain backup failed (non-fatal)")
    except Exception as e:
        if backup_complete:
            # Phase 1 succeeded but a later phase failed: keep the backup
            # so the user's photos/settings are recoverable, and say where.
            kept = os.path.join(protective_dir, "device_backup")
            print(f"[iOS27] Restore failed; protective backup kept at: {kept}")
            try:
                e.add_note(f"Protective backup kept at: {kept}")
            except AttributeError:
                pass  # Python < 3.11 — path is still in the log.
            raise
        # Backup never completed — nothing worth keeping, don't leak data.
        shutil.rmtree(protective_dir, ignore_errors=True)
        raise

    shutil.rmtree(protective_dir, ignore_errors=True)
    progress_callback(100)


# files is a list of FileToRestore objects
async def restore_files(files: list[FileToRestore], reboot: bool = False, lockdown_client: LockdownClient = None, progress_callback = lambda x: None):
    # create the files to be backed up
    files_list = [
    ]
    apps_list = []
    active_bundle_ids = []
    apps = None
    sorted_files = sorted(merge_duplicates(files), key=lambda x: (x.domain, x.restore_path), reverse=False)
    # add the file paths
    last_domain = ""
    last_path = ""
    exploit_only = True
    # extra check for system version to prevent sparserestore from restoring on iOS 18.1+
    passed_version_check = has_sparserestore_capability(lockdown_client)
    for file in sorted_files:
        if file.domain == "" or file.domain == "z":
            if passed_version_check:
                last_domain = concat_exploit_file(file, files_list, last_domain)
        else:
            last_domain, last_path = concat_regular_file(file, files_list, last_domain, last_path)
            exploit_only = False
            # add the app bundle to the list
            if last_domain.startswith("AppDomain"):
                bundle_id = last_domain.removeprefix("AppDomain-")
                if not bundle_id in active_bundle_ids:
                    # All AppDomain-* bundles MUST be registered in
                    # Manifest.plist's Applications dictionary, otherwise
                    # the device-side restore daemon will reject the domain
                    # with MBErrorDomain/205 ("Unknown domain name").
                    # This includes system apps like com.apple.PosterBoard.
                    if apps == None:
                        async with InstallationProxyService(lockdown=lockdown_client) as ips:
                            apps = await ips.get_apps(application_type="Any", calculate_sizes=False)
                    try:
                        app_info = apps[bundle_id]
                        active_bundle_ids.append(bundle_id)
                        apps_list.append(backup.AppBundle(
                            identifier=bundle_id,
                            path=app_info["Container"],
                            version=app_info.get("CFBundleVersion", "1.0"),
                            container_content_class="Data/Application"
                        ))
                    except (KeyError, Exception) as e:
                        print(
                            f"WARNING: AppDomain bundle '{bundle_id}'"
                            f" not found in installation proxy"
                            f" ({type(e).__name__}). AppDomain files"
                            f" may cause MBErrorDomain/205."
                        )
                        active_bundle_ids.append(bundle_id)

    # crash the restore to skip the setup (only works for exploit files, NOT on iOS 27+)
    ios_major = 0
    if lockdown_client is not None:
        try:
            ios_major = int(lockdown_client.product_version.split(".")[0])
        except (ValueError, IndexError, AttributeError):
            ios_major = 0
    if exploit_only and (lockdown_client is None or ios_major < 27):
        files_list.append(backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""))

    # create the backup
    back = backup.Backup(files=files_list, apps=apps_list)

    # iOS 27+: use three-phase protective backup + restore
    if ios_major >= 27:
        await _restore_ios27(back, reboot, lockdown_client, progress_callback)
        return

    for fi in files_list:
        print(f"{fi.domain}, {fi.path}")

    try:
        await perform_restore(backup=back, reboot=reboot, lockdown_client=lockdown_client, progress_callback=progress_callback)
    except (ConnectionTerminatedError, ssl.SSLEOFError, ConnectionAbortedError, ConnectionResetError):
        # These errors usually mean the device rebooted successfully before acknowledging the restore.
        # We catch them and treat the process as successful.
        print("Device disconnected during restore - this is expected as the device reboots.")
        # The device severing the connection mid-restore is treated as a
        # reboot (system/exploit files reboot on their own). But PosterBoard
        # (AppDomain-*) restores do NOT reboot the device, so if a reboot was
        # requested and the device is still reachable, reboot it explicitly
        # now. If it already rebooted, the reconnect fails and we continue.
        if reboot and lockdown_client is not None:
            await _reboot_device_after_disconnect(lockdown_client.udid)
        if progress_callback:
            progress_callback(100)
            
    except Exception as e:
        # If it's a different error, we still want to see it
        raise e


async def _reboot_device_after_disconnect(udid: str):
    """Reboot the device after a mid-restore disconnect, unless it already
    rebooted on its own. The connection was severed, so reconnect first:
    if the device already rebooted (system/exploit files) lockdown is down
    and the reconnect fails — that is expected, and we just continue."""
    try:
        new_ld = await create_using_usbmux(serial=udid, pair_timeout=15)
    except Exception:
        print("Device already rebooted (no lockdown service) - skipping explicit reboot.")
        return
    try:
        await reboot_device(reboot=True, lockdown_client=new_ld)
    except Exception as e:
        print(f"Failed to reboot device after disconnect: {e}")
    finally:
        try:
            await new_ld.close()
        except Exception:
            pass


def restore_file(fp: str, restore_path: str, restore_name: str, reboot: bool = False, lockdown_client: LockdownClient = None):
    # open the file and read the contents
    contents = open(fp, "rb").read()

    base_path = "/var/backup"
    if restore_path.startswith("/var/mobile/"):
        # required on iOS 17.0+ since /var/mobile is on a separate partition
        base_path = "/var/mobile/backup"

    # create the backup
    back = backup.Backup(files=[
        # backup.Directory("", "HomeDomain"),
        # backup.Directory("Library", "HomeDomain"),
        # backup.Directory("Library/Preferences", "HomeDomain"),
        # backup.ConcreteFile("Library/Preferences/temp", "HomeDomain", owner=501, group=501, contents=contents, inode=0),
        backup.Directory(
                "",
                f"SysContainerDomain-../../../../../../../..{base_path}{restore_path}",
                owner=501,
                group=501
            ),
        backup.ConcreteFile(
                "",
                f"SysContainerDomain-../../../../../../../..{base_path}{restore_path}{restore_name}",
                owner=501,
                group=501,
                contents=contents#b"",
                # inode=0
            ),
            backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
    ])

    try:
        asyncio.run(perform_restore(backup=back, reboot=reboot, lockdown_client=lockdown_client))
    except (ConnectionTerminatedError, ssl.SSLEOFError, ConnectionAbortedError, ConnectionResetError):
        pass