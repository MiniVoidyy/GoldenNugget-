from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
from pymobiledevice3.lockdown import create_using_usbmux
import asyncio

async def rec():
    lockdown_client = await create_using_usbmux()
    async with Mobilebackup2Service(lockdown_client) as mb:
        await mb.restore(
            str("/Users/username/Library/Application Support/Nugget/Backups"),
            system=True, copy=True, remove=False,
            reboot=True, source="XXX",
            skip_apps=False,
            progress_callback=(lambda v: print(f"progress: {v}"))
        )

asyncio.run(rec())
