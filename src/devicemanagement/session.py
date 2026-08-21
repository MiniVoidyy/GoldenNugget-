"""Single entry point for opening lockdown connections.

Every device conversation should use ``lockdown_session`` so connections are
always closed safely (a rebooted device makes ``close()`` raise, which must
never mask the real result).
"""
from contextlib import asynccontextmanager

from pymobiledevice3.lockdown import create_using_usbmux


@asynccontextmanager
async def lockdown_session(serial: str = None):
    """Open a lockdown connection to the device and close it safely on exit."""
    ld = await create_using_usbmux(serial=serial)
    try:
        yield ld
    finally:
        try:
            await ld.close()
        except Exception:
            pass