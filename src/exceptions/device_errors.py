"""Shared error classification for device backup/restore operations."""
import asyncio
import plistlib

import pymobiledevice3.exceptions as pm3_exc


def is_find_my_error(exc: BaseException) -> bool:
    """Recognize explicit Find My restore errors, including wrapped causes."""
    pending = [exc]
    inspected = set()
    while pending:
        current = pending.pop()
        if id(current) in inspected:
            continue
        inspected.add(id(current))
        if "find my" in str(current).casefold():
            return True
        pending.extend(cause for cause in
                       (current.__cause__, current.__context__)
                       if cause is not None)
        pending.extend(arg for arg in current.args
                       if isinstance(arg, BaseException))
    return False


def is_device_locked_error(exc: Exception) -> bool:
    """Check if an exception indicates the device is locked (ErrorCode 208)."""
    msg = str(exc)
    return "ErrorCode" in msg and ("208" in msg or "Device locked" in msg or "MBErrorDomain" in msg)


def is_connection_error(exc: Exception) -> bool:
    """Check if an exception is a transient connection failure worth retrying."""
    msg = str(exc).lower()
    return isinstance(exc, (
        pm3_exc.ConnectionTerminatedError,
        ConnectionError,
        OSError,
        asyncio.TimeoutError,
    )) or "connection" in msg or "incomplete" in msg or "terminated" in msg


def is_device_lock_required_error(exc: Exception) -> bool:
    """True when lockdown refused to start a service because the device is locked.

    Distinct from :func:`is_device_locked_error`, which sniffs the
    mobilebackup2 "ErrorCode 208" text. A *paired* lockdown session can be
    established while the device still sits at the lock screen, so
    ``StartService`` answers ``PasswordProtected`` even though nothing is
    actually wrong: the device just has to be unlocked. That makes it a
    wait-and-retry condition, not a failure.
    """
    if isinstance(exc, (pm3_exc.PasswordRequiredError, pm3_exc.PasscodeRequiredError)):
        return True
    msg = str(exc)
    return "PasswordProtected" in msg or "PasscodeRequired" in msg


def is_transient_restore_error(error) -> bool:
    """True for Phase 3 errors that mean 'device still booting, try again'."""
    if is_find_my_error(error):
        return False
    name = type(error).__name__
    msg = str(error)
    # ssl.SSLError subclasses OSError, so this covers SSL drops too.
    if isinstance(error, (pm3_exc.ConnectionTerminatedError, OSError)):
        return True
    if "InvalidService" in name:
        return True
    if "NotEnoughDiskSpace" in str(error):
        return True  # device-side purge request — retry after cleanup
    # MBErrorDomain/1: SpringBoard not ready for a restore yet.
    if "SpringBoard" in msg and "ready for a restore" in msg:
        return True
    # A malformed plist over the restore channel. On a freshly-rebooted iOS 27
    # device this is almost always the mobilebackup2 tunnel being torn down or
    # truncated mid-handshake, not a broken backup — retrying on a fresh
    # service reconnects and completes the restore. Aborting on the first
    # occurrence strands the user right after Phase 2 wiped the device (the
    # exact data-loss route seen with "InvalidFileException in Phase 3").
    if isinstance(error, plistlib.InvalidFileException):
        return True
    if "parse_plist invalid data" in msg:
        return True
    return "start" in msg.lower() and "service" in msg.lower()
