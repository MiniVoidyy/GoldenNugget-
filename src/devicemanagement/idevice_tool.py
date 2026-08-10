"""Thin wrapper over the libimobiledevice ``idevice*`` command-line tools.

The device operations that touch the C crypto stack (backup, restore,
reboot) run inside the ``idevice*`` child process instead of the GUI
process. That way a SEGV in OpenSSL/sslpsk/anything linked into those
binaries can never take the application down with it.

Binary resolution order:
  1. ``$GOLDENNUGGET_IDEVICE_DIR`` (a directory holding the binaries)
  2. ``<PyInstaller _MEIPASS>/idevice`` (bundled binaries)
  3. ``PATH``

Set ``GOLDENNUGGET_FORCE_PM3=1`` to bypass the wrapper and use the
in-process pymobiledevice3 code paths (exactly what the base does).
"""

import os
import re
import shutil
import subprocess
import sys
import time
from typing import Callable, List, Optional


class ToolError(RuntimeError):
    """Raised when an idevice* tool is missing or exits non-zero."""


class ToolNotFound(ToolError):
    """Raised when an idevice* binary cannot be located."""


# Text markers in a tool's stderr/stdout that indicate the device dropped the
# connection mid-operation (usually because it rebooted during the restore).
# "Could not receive from mobilebackup2" / "Restore Aborted" are what
# idevicebackup2 prints when the device severs the connection after it has
# received the system files (iOS 26+ reboots to apply them).
_DISCONNECT_MARKERS = (
    "disconnect", "connection lost", "got disconnected", "not connected",
    "no device", "unable to connect", "device is not connected",
    "broken pipe", "connection reset",
    "could not receive from mobilebackup2", "restore aborted",
)

# Text markers for the mobilebackup2 handshake failing between split applies.
# Right after a reboot the device's backupd is not ready yet and idevicebackup2
# reports "Could not perform backup protocol version exchange, error code -1".
# This is transient — waiting and retrying works — unlike a genuine rejection.
_TRANSIENT_MARKERS = (
    "backup protocol version exchange",
    "protocol version exchange",
    "could not perform backup",
    "unable to perform backup",
)


def looks_like_device_reboot(output: str) -> bool:
    """Best-effort guess whether a failed tool run was just the device
    rebooting mid-restore (expected) rather than the device rejecting it."""
    lowered = output.lower()
    return any(marker in lowered for marker in _DISCONNECT_MARKERS)


def looks_like_transient_failure(output: str) -> bool:
    """True when the failure looks like the device-side backup service was not
    ready yet (e.g. it is still booting after a reboot). Such failures resolve
    on their own after a short wait and are safe to retry."""
    lowered = output.lower()
    return any(marker in lowered for marker in _TRANSIENT_MARKERS)


def looks_like_transfer_started(output: str) -> bool:
    """True if the tool output shows the device had already begun pulling
    files, i.e. the restore was actually in progress and was not rejected
    up front. Used together with looks_like_device_reboot() so an instant
    refusal is never mistaken for a mid-restore reboot."""
    lowered = output.lower()
    return ("sending '" in lowered
            or "sending ./" in lowered
            or "wrote restoreapplications.plist" in lowered)


def _binary_suffix() -> str:
    return ".exe" if os.name == "nt" else ""


def _tool_dirs() -> List[str]:
    dirs: List[str] = []
    env_dir = os.environ.get("GOLDENNUGGET_IDEVICE_DIR")
    if env_dir:
        dirs.append(env_dir)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(os.path.join(meipass, "idevice"))
    return dirs


def find_tool(name: str) -> Optional[str]:
    """Locate an idevice* binary, or None if it is not available."""
    for d in _tool_dirs():
        candidate = os.path.join(d, name + _binary_suffix())
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which(name)


def available(name: str) -> bool:
    return find_tool(name) is not None


def _require_tool(name: str) -> str:
    tool = find_tool(name)
    if tool is None:
        raise ToolNotFound(
            f"Could not find '{name}'. Install libimobiledevice "
            "(idevicebackup2/idevicediagnostics) or set "
            "GOLDENNUGGET_IDEVICE_DIR to the folder holding the binaries.")
    return tool


def use_wrapper() -> bool:
    return not os.environ.get("GOLDENNUGGET_FORCE_PM3")


# idevicebackup2 prints progress like "Backup progress: 3/19 (15%)".
_PROGRESS_PERCENT_RE = re.compile(r"(\d+)\s*%")
_PROGRESS_FRACTION_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def _extract_progress(line: str) -> Optional[float]:
    m = _PROGRESS_PERCENT_RE.search(line)
    if m:
        return min(100.0, float(m.group(1)))
    m = _PROGRESS_FRACTION_RE.search(line)
    if m:
        numerator = float(m.group(1))
        denominator = float(m.group(2))
        if denominator > 0:
            return min(100.0, numerator / denominator * 100.0)
    return None


def _run_streaming(cmd: List[str], progress_callback: Optional[Callable] = None) -> None:
    """Run a command, stream its stdout lines and raise ToolError on failure."""
    output_lines: List[str] = []
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding="utf-8", errors="replace")
    except OSError as e:
        raise ToolError(f"Failed to start {cmd[0]}: {e}") from e

    last_progress = [0.0]

    def _report(text: str):
        if progress_callback is None:
            return
        progress_callback(text)

    if proc.stdout is not None:
        for raw_line in proc.stdout:
            line = raw_line.rstrip()
            output_lines.append(line)
            if line:
                pct = _extract_progress(line)
                if pct is not None and pct >= last_progress[0]:
                    last_progress[0] = pct
                    _report(pct)
                else:
                    _report(line)

    returncode = proc.wait()
    if returncode != 0:
        tail = "\n".join(output_lines[-12:])
        raise ToolError(
            f"{os.path.basename(cmd[0])} failed (exit {returncode}).\n{tail}")


def device_list() -> List[str]:
    """Return the list of connected device UDIDs (empty on failure)."""
    tool = find_tool("idevice_id")
    if tool is None:
        return []
    try:
        result = subprocess.run(
            [tool, "-l"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def backup(udid: str, backup_dir: str, full: bool = True,
           progress_callback: Optional[Callable] = None) -> None:
    """Run ``idevicebackup2 backup [--full] <backup_dir>``.

    ``backup_dir`` receives the backup files directly (the standard
    idevicebackup2 layout — Manifest.plist/Manifest.db at its root).
    """
    if not use_wrapper():
        raise ToolError("idevice_tool.backup bypassed by GOLDENNUGGET_FORCE_PM3")
    tool = _require_tool("idevicebackup2")
    cmd = [tool, "-u", udid, "backup"]
    if full:
        cmd.append("--full")
    cmd.append(backup_dir)
    _run_streaming(cmd, progress_callback)


def restore(udid: str, backup_dir: str, system: bool = True, reboot: bool = False,
            progress_callback: Optional[Callable] = None) -> None:
    """Run ``idevicebackup2 restore [--system] [--no-reboot] <backup_dir>``.

    ``-s .`` makes idevicebackup2 treat ``backup_dir`` as the source backup
    folder itself (files at its root), matching the base flow's
    ``source="."`` semantics and the layout produced by ``write_to_directory``.
    Without it, idevicebackup2 would look for ``backup_dir/<udid>/Info.plist``
    and reject the restore with exit 255.
    """
    if not use_wrapper():
        raise ToolError("idevice_tool.restore bypassed by GOLDENNUGGET_FORCE_PM3")
    tool = _require_tool("idevicebackup2")
    cmd = [tool, "-u", udid, "-s", ".", "restore"]
    if system:
        cmd.append("--system")
    if not reboot:
        cmd.append("--no-reboot")
    cmd.append(backup_dir)
    _run_streaming(cmd, progress_callback)


def reboot(udid: str) -> None:
    """Request a device restart via ``idevicediagnostics restart``."""
    if not use_wrapper():
        raise ToolError("idevice_tool.reboot bypassed by GOLDENNUGGET_FORCE_PM3")
    tool = _require_tool("idevicediagnostics")
    _run_streaming([tool, "-u", udid, "restart"])


def wait_for_device(udid: str, timeout: float = 300.0,
                    poll_interval: float = 5.0) -> bool:
    """Poll ``idevice_id -l`` until the device shows up or the timeout hits."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if udid in device_list():
            return True
        time.sleep(poll_interval)
    return False
