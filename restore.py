#! python3

from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
from pymobiledevice3.lockdown import create_using_usbmux
import asyncio
import sys

async def main(argv: list):
    lockdown_client = await create_using_usbmux()
    async with Mobilebackup2Service(lockdown_client) as mb:
        await mb.restore(
            str(argv[1]),
            system=True, copy=True, remove=False,
            reboot=True, source=argv[2],
            skip_apps=False,
            progress_callback=(lambda v: print(f"progress: {v}\r"))
        )
        print("Restore done!")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: restore.py <backup path> <device UUID>", file=sys.stderr)
        exit(1)
    asyncio.run(main(sys.argv))
