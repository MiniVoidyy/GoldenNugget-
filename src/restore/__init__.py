import asyncio
import time

from tempfile import TemporaryDirectory
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
from pymobiledevice3.exceptions import PyMobileDevice3Exception, ConnectionTerminatedError
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.lockdown import LockdownClient

from . import backup
from src.devicemanagement import idevice_tool

RESTORE_RETRIES = 4
RESTORE_RETRY_DELAY = 15

async def reboot_device(reboot: bool = False, lockdown_client: LockdownClient = None):
    if reboot and lockdown_client != None:
        print("Success! Rebooting your device...")
        if idevice_tool.available("idevicediagnostics") and idevice_tool.use_wrapper():
            # run the restart in the idevicediagnostics child process so a
            # SEGV in its crypto stack cannot take the GUI down
            await asyncio.to_thread(idevice_tool.reboot, lockdown_client.udid)
        else:
            async with DiagnosticsService(lockdown_client) as diagnostics_service:
                await diagnostics_service.restart()
        print("Remember to turn Find My back on!")

async def perform_restore(backup: backup.Backup, reboot: bool = False, lockdown_client: LockdownClient = None, progress_callback = lambda x: None):
    own_lockdown = (lockdown_client is None)
    try:
        with TemporaryDirectory() as backup_dir:
            backup.write_to_directory(Path(backup_dir))

            if own_lockdown:
                lockdown_client = await create_using_usbmux()
            if idevice_tool.available("idevicebackup2") and idevice_tool.use_wrapper():
                # Run the restore through idevicebackup2 (child process) so a
                # SEGV in the C crypto stack cannot take the GUI down. The
                # backup directory layout is identical to what idevicebackup2
                # restore expects (files at the directory root).
                last_progress = [0.0]
                restore_started = time.monotonic()

                def _wrap_progress(value):
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        last_progress[0] = max(last_progress[0], float(value))
                    progress_callback(value)

                # After a reboot (e.g. between split tendie applies) the
                # device's backupd may not be ready yet and the
                # mobilebackup2 handshake fails with "Could not perform
                # backup protocol version exchange". That is transient —
                # wait and retry instead of aborting the whole apply.
                for attempt in range(RESTORE_RETRIES):
                    try:
                        await asyncio.to_thread(
                            idevice_tool.restore,
                            lockdown_client.udid, backup_dir,
                            system=True, reboot=False,
                            progress_callback=_wrap_progress,
                        )
                        break
                    except idevice_tool.ToolError as e:
                        # A failed connection near the end of the restore usually
                        # means the device rebooted mid-restore (expected for
                        # crash_on_purpose/exploit-only applies). Raise
                        # ConnectionTerminatedError so the caller treats it as a
                        # successful reboot, matching the base behaviour. An
                        # instant disconnect with no progress means the device
                        # REJECTED the restore before receiving any files — that
                        # must surface as a real error.
                        if (idevice_tool.looks_like_device_reboot(str(e))
                                and (last_progress[0] > 0
                                     or idevice_tool.looks_like_transfer_started(str(e))
                                     or time.monotonic() - restore_started >= 15)):
                            raise ConnectionTerminatedError() from e
                        if (idevice_tool.looks_like_transient_failure(str(e))
                                and attempt < RESTORE_RETRIES - 1):
                            print(f"Restore handshake failed, retrying in {RESTORE_RETRY_DELAY}s ({attempt + 2}/{RESTORE_RETRIES}): {e}")
                            await asyncio.sleep(RESTORE_RETRY_DELAY)
                            continue
                        raise
            else:
                async with Mobilebackup2Service(lockdown_client) as mb:
                    # skip_apps=False: required for AppDomain-* domains (PosterBoard).
                    # When True, the device-side restore daemon skips restoring
                    # data for every app in Manifest.plist's Applications dict.
                    # PosterBoard (the only tweak using AppDomain-*) must be
                    # registered there to avoid MBErrorDomain/205.
                    # Note: may trigger an iOS passcode prompt — unlock the
                    # device to proceed.
                    await mb.restore(backup_dir, system=True, reboot=False, copy=False, source=".", progress_callback=progress_callback, skip_apps=False)
            # reboot the device
            await reboot_device(reboot, lockdown_client)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            print("Find My must be disabled in order to use this tool.")
            print("Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.")
            raise e
        elif "crash_on_purpose" not in str(e):
            raise e
        else:
            await reboot_device(reboot, lockdown_client)
    finally:
        # If we created this lockdown_client ourselves, close it safely.
        # After a device reboot the connection is severed and close() will
        # raise ConnectionTerminatedError — suppress it to avoid misleading
        # "Connection Lost" errors in upstream callers.
        if own_lockdown and lockdown_client is not None:
            try:
                await lockdown_client.close()
            except Exception:
                pass
