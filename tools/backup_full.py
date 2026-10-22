"""Full device backup (async pm3 API). Usage: python3 tools/backup_full.py OUTDIR"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.usbmux import list_devices

from src.restore.protective import ProtectiveBackupService


def progress(msg):
    if isinstance(msg, str):
        print(msg, flush=True)


async def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/opencode/full_backup"
    ds = await list_devices()
    usb = [d for d in ds if d.is_usb]
    if not usb:
        print("no device")
        return 1
    ld = await create_using_usbmux(serial=usb[0].serial)
    os.makedirs(out, exist_ok=True)
    async with ProtectiveBackupService(ld) as mb:
        await mb.backup(full=True, backup_directory=out,
                        progress_callback=progress)
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))