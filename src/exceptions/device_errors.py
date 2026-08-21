"""Shared error classification for device backup/restore operations."""
import asyncio

import pymobiledevice3.exceptions as pm3_exc


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
