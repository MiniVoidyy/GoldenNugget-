"""
AFC-backed parallel media backup/restore channel.

On iOS 27 the three-phase restore wipes the device (security recovery), so
photos/videos must survive on this computer between Phase 2 and Phase 3. They
are normally carried inside the protective mobilebackup2 backup, which is
slow (the whole Media tree uploads through DeviceLink). When
``use_afc_media`` is on, the *bulk* photo trees (``DCIM``,
``PhotoStreamsData`` — the actual photo/video files) are instead pulled over
plain ``com.apple.afc`` in *parallel* with the mobilebackup2 backup of
everything else, and pushed back over the same channel during Phase 5
(after the Phase 4 reboot and reconnect, on the freshly-booted device).

The scope is deliberately narrow: only the top-level Media trees in
``AFC_MEDIA_TREES`` go over AFC. ``PhotoData`` — the photo library database
(CPLAssets) plus its protected metadata (``PhotoData/UBF`` is NOT listable
over the media AFC service; it fails with AFC error 10 / PERM_DENIED on
iOS 27) — stays inside the mobilebackup2 backup, which reads it natively.
The mobilebackup2 upload filter and the manifest prune both exclude the same
``AFC_MEDIA_TREES`` so the split stays coherent end-to-end (no wasted
uploads, no manifest rows pointing at payloads that were never written).

Design rules:
- Progress is reported as strings only (never numbers): the mobilebackup2
  numbers drive the progress bar, and a concurrent numeric feed would corrupt
  it.
- Pull-side failures are fatal by default: the media dir is the ONLY copy of
  the user's photos after Phase 2 wipes the device, so a silent drop is data
  loss. Callers that need best-effort pass ``on_error="warn"``.
- Symlinks are skipped (never copied as files): following them could escape
  the Media tree and would duplicate content.
"""

# PEP 810: defer operation-only dependencies on Python 3.15+; eager on older Python.
__lazy_modules__ = (
    "pymobiledevice3.services.afc",
)

from src.devicemanagement.progress_status import OperationStatus

import asyncio
import json
import os
import posixpath
from pathlib import Path

from src.controllers.archive_safety import safe_member
import time
from contextlib import AsyncExitStack, asynccontextmanager

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import MAXIMUM_READ_SIZE, AfcService, AfcError
from pymobiledevice3.exceptions import AfcException, AfcFileNotFoundError

from src.exceptions.device_errors import (
    is_connection_error,
    is_device_lock_required_error,
)
from src.exceptions.nugget_exception import NuggetException
from src.utils.log_util import log_info, log_warn

AFC_MEDIA_DIRNAME = "afc_media"

# Marker written next to a media store once a pull has completed end to end.
# The store is the ONLY copy of the user's photos between the wipe and Phase 5,
# so "the folder is not empty" is NOT proof that it is intact: a cancelled or
# interrupted pull leaves a partial tree behind that looks perfectly usable.
# Everything that decides whether the media trees may be dropped from the backup
# must consult this marker instead.
MEDIA_STATE_FILE = ".media_state.json"

# Top-level Media trees moved to the AFC channel. Everything else under
# /var/mobile/Media (notably PhotoData/) stays in the mobilebackup2 backup:
# some of its subdirectories (PhotoData/UBF on iOS 27) are unlistable over the
# media AFC service, and restoring the photo library DB via mobilebackup2
# keeps the library consistent with the DCIM originals we push back over AFC.
AFC_MEDIA_TREES = frozenset({"DCIM", "PhotoStreamsData"})


def afc_media_enabled(pref_enabled: bool = True) -> bool:
    """Whether the AFC media channel is active for a given apply.

    The environment ``GOLDENNUGGET_NO_AFC_MEDIA=1`` kill switch always wins —
    it force-disables the channel the way ``GOLDENNUGGET_NO_BACKUP_CACHE``
    force-disables the backup cache.
    """
    return pref_enabled and os.environ.get("GOLDENNUGGET_NO_AFC_MEDIA") != "1"


def afc_media_dir_for(backup_root: str) -> str:
    """Media directory paired with a protective backup run.

    ``backup_root`` is ``<run dir>/device_backup``; the media tree lives next
    to it inside the same run dir (``<run dir>/afc_media``) so that run-level
    cleanup (prune_protective_backups, failure rmtree) reclaims both together.
    """
    return os.path.join(os.path.dirname(os.path.abspath(backup_root)),
                        AFC_MEDIA_DIRNAME)


def _is_afc_link(stat: dict) -> bool:
    return bool(stat) and stat.get("st_ifmt") == "S_IFLNK"


# ---- media store verification -------------------------------------------
#
# A media store is only trustworthy when a pull ran to completion. That fact is
# recorded in a marker file next to the tree; anything that would exclude the
# media trees from the backup (and therefore delete the only copy of the user's
# photos) has to require this marker.

def media_store_state(media_root: str) -> dict | None:
    """Parsed completion marker for ``media_root``, or ``None`` if there is none."""
    if not media_root:
        return None
    try:
        with open(os.path.join(media_root, MEDIA_STATE_FILE),
                  encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def _media_inventory(media_root: str) -> dict[str, int]:
    """Inventory real payloads; host bookkeeping and incomplete writes stay local."""
    inventory = {}
    def unreadable(error):
        raise error

    for dirpath, dirnames, filenames in os.walk(media_root, onerror=unreadable):
        if any(os.path.islink(os.path.join(dirpath, name)) for name in dirnames):
            raise ValueError("Media store contains a linked directory")
        for name in filenames:
            if name in (MEDIA_STATE_FILE, MEDIA_STATE_FILE + '.tmp') or name.endswith('.part'):
                continue
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                raise ValueError("Media store contains a linked file")
            relative = os.path.relpath(path, media_root).replace(os.sep, '/')
            inventory[relative] = os.path.getsize(path)
    return inventory


def media_store_verified(media_root: str) -> bool:
    """Require every file recorded by the pull, at its exact recorded size.

    Legacy aggregate-only markers cannot prove completeness and force a fresh
    pull. Extra historical files never substitute for a missing current file.
    """
    state = media_store_state(media_root)
    if not state or state.get('complete') is not True or state.get('version') != 2:
        return False
    entries = state.get('entries')
    if not isinstance(entries, dict) or not entries or not os.path.isdir(media_root):
        return False
    try:
        total = 0
        root = Path(media_root).resolve()
        for relative, size in entries.items():
            if (not isinstance(relative, str) or not safe_member(relative)
                    or type(size) is not int or size < 0):
                return False
            target = root.joinpath(*relative.split('/'))
            if (not target.resolve().is_relative_to(root) or target.is_symlink()
                    or not target.is_file() or target.stat().st_size != size):
                return False
            total += size
        return (type(state.get('files')) is int and state['files'] == len(entries)
                and type(state.get('bytes')) is int and state['bytes'] == total)
    except (OSError, ValueError):
        return False


def recovery_media_dir(backup_root: str, udid: str, cache_base=None) -> str:
    """Resolve media from the selected backup's metadata, never another cache."""
    if cache_base is not None:
        base = Path(cache_base)
        media = base / 'media' / udid
        try:
            info = json.loads((base / f'{udid}.json').read_text(encoding='utf-8'))
            if isinstance(info, dict) and 'media_afc' in info:
                return str(media) if info['media_afc'] else ''
        except (OSError, ValueError):
            pass
        return str(media) if media.is_dir() else ''
    media = afc_media_dir_for(backup_root)
    required = Path(backup_root).parent / '.afc_media_required'
    return media if os.path.isdir(media) or required.exists() else ''


def describe_media_store(media_root: str) -> str:
    """One-line summary of a media store, for logs and error messages."""
    state = media_store_state(media_root) or {}
    files = int(state.get("files") or 0)
    mib = int(state.get("bytes") or 0) / (1024 * 1024)
    return (f"{media_root}: {files} files / {mib:.1f} MB "
            f"({'verified' if media_store_verified(media_root) else 'NOT verified'})")


def _write_media_state(media_root: str, files: int, bytes_: int,
                       skipped: int, entries: dict[str, int] | None = None) -> None:
    """Record a completed pull so later applies may treat the store as intact."""
    if entries is None:
        try:
            entries = _media_inventory(media_root)
        except (OSError, ValueError):
            _invalidate_media_state(media_root, "could not inventory payloads")
            return
    state = {
        "version": 2,
        "entries": entries,
        "complete": True,
        "files": int(files),
        "bytes": int(bytes_),
        "skipped": int(skipped),
        "ts": time.time(),
    }
    tmp = os.path.join(media_root, MEDIA_STATE_FILE + ".tmp")
    try:
        os.makedirs(media_root, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, os.path.join(media_root, MEDIA_STATE_FILE))
    except OSError as e:
        log_warn(f"AFC media: could not write the media store marker "
                 f"({e}) — the store stays unverified")


def _invalidate_media_state(media_root: str, reason: str) -> None:
    """Drop the completion marker after a failed/cancelled pull.

    A partially written media tree must never be presented as a complete copy of
    the user's photos, or the next apply would delete the backup's copy of the
    media trees and push only the fragment that is left.
    """
    if not media_root:
        return
    had_state = media_store_state(media_root) is not None
    try:
        os.remove(os.path.join(media_root, MEDIA_STATE_FILE))
    except OSError:
        pass
    if had_state:
        log_warn(f"AFC media: media store marker dropped ({reason}) — "
                 f"{media_root} is now UNVERIFIED and must not be used as the "
                 f"only copy of the photos")


def _progress_str(action: str, done_files: int, total_files: int,
                  done_bytes: int, total_bytes: int) -> str:
    if total_bytes > 0:
        pct = 100.0 * done_bytes / total_bytes
        mb = done_bytes / (1024 * 1024)
        return (f"{action}... {pct:.0f}% ({done_files}/{total_files} files, "
                f"{mb:.1f} MB)")
    return f"{action}... {done_files}/{total_files} files"


async def _pull_one(afc, src: str, dst: str, stat) -> int:
    """Stream one regular file from the device to ``dst``, returning bytes.

    The write is verified against the size the device reported and lands through
    a temp file, so a short read can never leave a truncated file behind that a
    later size-based ``diff`` would accept as already pulled. That failure mode
    is not cosmetic: a truncated MP4/MOV still *is* recognised by Photos but
    will not play (its ``moov`` atom is at the tail), and this is the branch
    every file over ``MAXIMUM_READ_SIZE`` — i.e. essentially every video —
    takes, while the small-file branch below reads exactly ``st_size``.
    """
    size = int(stat.get("st_size", 0))
    if size <= MAXIMUM_READ_SIZE:
        data = await afc.get_file_contents(src)
        # ``size`` is 0 when the device did not report one; only a real
        # advertised size can be violated
        if size and len(data) != size:
            raise NuggetException(
                f"AFC media: short read on {src} — device reported {size} bytes, "
                f"got {len(data)}")
        _atomic_write(dst, data)
        return len(data)

    tmp = dst + ".part"
    handle = await afc.fopen(src)
    try:
        written = 0
        with open(tmp, "wb") as f:
            while written < size:
                to_read = min(MAXIMUM_READ_SIZE, size - written)
                chunk = await afc.fread(handle, to_read)
                if not chunk:
                    # premature EOF: the file is incomplete, not finished
                    raise NuggetException(
                        f"AFC media: connection ended mid-file on {src} — "
                        f"got {written} of {size} bytes")
                f.write(chunk)
                written += len(chunk)
    except BaseException:
        # never leave a partial file the diff would treat as complete
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    finally:
        await afc.fclose(handle)
    os.replace(tmp, dst)
    return written


def _atomic_write(dst: str, data: bytes) -> None:
    """Write ``data`` to ``dst`` through a temp file + rename."""
    tmp = dst + ".part"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dst)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


async def _list_afc_tree(afc, dirpath: str, entries: list,
                         on_error: str, failed: list[str]) -> None:
    """Recursively collect the regular files under ``dirpath`` into ``entries``.

    Mirrors the on-device layout: each item is (src, rel, stat) where ``rel``
    is the path relative to the AFC root (``DCIM/100APPLE/IMG_0001.JPG``).
    A warned enumeration failure still makes the store incomplete: unknown
    directory contents cannot be excluded safely from the native backup.
    """
    try:
        children = await afc.listdir(dirpath)
    except Exception as e:
        msg = f"AFC media: cannot list {dirpath or '/'}: {e}"
        if on_error == "warn":
            log_warn(msg + " — skipping this directory")
            failed.append(dirpath)
            return
        raise NuggetException(msg) from e
    for name in sorted(children):
        if name in (".", ".."):
            continue
        src = posixpath.join(dirpath, name)
        rel = src.lstrip("/")
        try:
            st = await afc.stat(src)
            if _is_afc_link(st):
                log_info(f"AFC media: skipping symlink {src}")
                continue
            if st.get("st_ifmt") == "S_IFDIR":
                await _list_afc_tree(afc, src, entries, on_error, failed)
            else:
                entries.append((src, rel, st))
        except Exception as e:
            msg = f"AFC media: could not stat {src}: {e}"
            if on_error != "warn":
                raise NuggetException(msg) from e
            log_warn(msg + " — skipping this entry")
            failed.append(src)


async def backup_media_via_afc(lockdown_client, media_root: str,
                               progress_callback=None,
                               on_error: str = "raise",
                               diff: bool = False) -> dict:
    """Pull the bulk photo trees over AFC into ``media_root``.

    Walks only the top-level Media trees named by ``AFC_MEDIA_TREES`` (DCIM,
    PhotoStreamsData) under the AFC root and mirrors every regular file into
    ``media_root`` preserving the on-device layout. Returns a tally dict
    ``{"files": int, "bytes": int, "skipped": int}``.

    With ``diff=True`` a local file that already exists at the same size is
    left untouched, so only new/changed objects are pulled — that is the
    cache refresh path, where ``media_root`` is the persistent per-device
    media store from a previous run (the first pull is still a full one).
    Extra local files (deleted on the device) are never removed: the media
    dir is the ONLY copy of the user's photos after a wipe, so deleting
    anything here would be data loss.
    """
    root = os.path.abspath(media_root)
    os.makedirs(root, exist_ok=True)

    def _log(value):
        if progress_callback is not None and not isinstance(value, (int, float)):
            progress_callback(value)

    if os.path.isdir(root) and os.listdir(root):
        log_info(f"AFC media pull: {root} already populated — "
                 f"{'diff refresh (pull only new/changed)' if diff else 'full refresh'}")
    # Drop the old claim BEFORE touching anything: this pull is about to rewrite
    # files in the store, so the previous run's "verified" is already stale. It
    # also covers the case the except-branch cannot — a hard process kill in the
    # middle of the pull — which would otherwise leave the marker claiming a
    # complete copy of a half-rewritten store.
    _invalidate_media_state(root, "a new pull is starting")
    try:
        result = await _backup_media_tree(afc_lockdown_client=lockdown_client, root=root,
                                          diff=diff, on_error=on_error,
                                          progress_callback=_log)
        return result
    except BaseException as e:
        # Covers per-file failures AND cancellation (the parallel task is
        # cancelled when the mobilebackup2 backup fails). Either way the store is
        # now a fragment: make sure no later apply can mistake it for a
        # complete copy of the user's photos.
        _invalidate_media_state(root, f"pull did not finish ({type(e).__name__})")
        raise


async def _backup_media_tree(afc_lockdown_client, root: str, diff: bool,
                             on_error: str, progress_callback) -> dict:
    tally = {"files": 0, "bytes": 0, "skipped": 0}
    async with AfcService(afc_lockdown_client) as afc:
        entries: list = []
        failed: list[str] = []
        root_children = await afc.listdir("/")
        for name in sorted(root_children):
            if name in (".", ".."):
                continue
            if name not in AFC_MEDIA_TREES:
                log_info(f"AFC media: leaving {name} to the mobilebackup2 "
                         "backup (out of AFC scope)")
                continue
            await _list_afc_tree(afc, f"/{name}", entries, on_error, failed)

        total_files = len(entries)
        total_bytes = sum(int(st.get("st_size", 0)) for _src, _rel, st in entries)

        done_files = 0
        done_bytes = 0
        skipped = 0
        for src, rel, st in entries:
            dst = os.path.join(root, *rel.split("/"))
            if diff:
                try:
                    if (os.path.getsize(dst) == int(st.get("st_size", 0))):
                        # Same size on both ends — already local, skip the pull.
                        skipped += 1
                        done_files += 1
                        continue
                except OSError:
                    pass  # file missing locally -> pull it
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            n = 0
            try:
                n = await _pull_one(afc, src, dst, st)
            except Exception as e:
                msg = f"AFC media: failed to pull {src}: {e}"
                if on_error == "warn":
                    log_warn(msg)
                    failed.append(src)
                else:
                    raise NuggetException(msg) from e
            done_files += 1
            done_bytes += n
            if done_files % 25 == 0 or done_files == total_files:
                progress_callback(_progress_str(
                    "Backing up photos/videos over AFC", done_files,
                    total_files, done_bytes, total_bytes))

        log_info(f"AFC media pull complete: {total_files} files, "
                 f"{total_bytes / (1024 * 1024):.1f} MB"
                 + (f" ({skipped} already present, skipped)" if skipped else ""))
        tally["files"] = total_files
        tally["bytes"] = total_bytes
        tally["skipped"] = skipped
        if failed:
            # a store with holes in it is not a copy of the photos: leave it
            # unmarked so the apply refuses to treat it as the media carrier
            log_warn(f"AFC media pull: {len(failed)} files skipped on error "
                     f"(e.g. {failed[:3]}) — media store left UNVERIFIED")
            tally["failed"] = failed
        else:
            _write_media_state(root, total_files, total_bytes, skipped,
                               {rel: int(st.get("st_size", 0))
                                for _src, rel, st in entries})
    return tally


async def _push_one(afc, src: str, remote_rel: str) -> int:
    """Push one local file onto the device, returning bytes written."""
    size = os.path.getsize(src)
    if size <= MAXIMUM_READ_SIZE:
        with open(src, "rb") as f:
            await afc.set_file_contents(remote_rel, f.read())
        return size
    handle = await afc.fopen(remote_rel, "w")
    try:
        with open(src, "rb") as f:
            while True:
                chunk = f.read(MAXIMUM_READ_SIZE)
                if not chunk:
                    break
                await afc.fwrite(handle, chunk)
        # a streaming write is the one that can end up half-written on the
        # device, so confirm what actually landed before reporting success
        st = await afc.stat(remote_rel)
        got = st.get("st_size") if st else None
        if got != size:
            raise NuggetException(
                f"AFC media: {remote_rel} was written short on the device "
                f"({got} of {size} bytes)")
        return size
    finally:
        await afc.fclose(handle)


# Phase 5 runs right after a reboot, and lockdownd answers StartService with
# PasswordProtected until the device is unlocked. A *paired* lockdown session
# is established happily while the device still sits at the lock screen, so
# _wait_for_device() returning is NOT evidence that services will start -- the
# first AFC open routinely fails on a device that is not actually broken. The
# media store is the only copy of the user's photos at that point, so give them
# a real window to unlock instead of failing the apply on a locked screen.
_AFC_OPEN_TIMEOUT = 5 * 60
_AFC_OPEN_INITIAL_DELAY = 2.0
_AFC_OPEN_MAX_DELAY = 15.0
# Pure safety net so the wait loop is finite by construction, no matter what
# the clock does. The real budget is the timeout above (~30 attempts at the
# capped delay), so this never fires in practice -- it only stops a runaway
# loop on a hostile/broken timing condition.
_AFC_OPEN_MAX_ATTEMPTS = 400


@asynccontextmanager
async def open_afc_for_media(lockdown_client, progress_callback=None,
                             prompt_choice=None, unlock_prompt=None,
                             timeout: float = _AFC_OPEN_TIMEOUT,
                             refresh_client: bool = False):
    """Open the AFC service, waiting out a locked device.

    Only the *connect* is retried. Once the service is up the caller's body
    runs exactly once, so a failure halfway through a push is never silently
    re-run (that would risk re-writing files the device already has).

    ``prompt_choice``/``unlock_prompt`` are the Abort/Resume escape hatch used
    once the wait budget is spent, mirroring ``_wait_for_device``. They are
    passed in (title, text) rather than built here so this module stays
    importable without Qt -- the offline AFC tests run on a bare interpreter.
    """
    def _log(value):
        if progress_callback is not None and not isinstance(value, (int, float)):
            progress_callback(value)

    while True:
        start = time.monotonic()
        deadline = start + timeout
        delay = _AFC_OPEN_INITIAL_DELAY
        last_error = None
        announced = False
        attempt = 0
        reconnect = refresh_client
        while True:
            attempt += 1
            fresh_client = None
            afc = None
            try:
                client = lockdown_client
                if reconnect:
                    fresh_client = await create_using_usbmux(
                        serial=lockdown_client.identifier, connection_type="USB",
                        autopair=False,
                        usbmux_address=getattr(lockdown_client, "usbmux_address", None))
                    client = fresh_client
                afc = AfcService(client)
                service = await afc.__aenter__()
            except Exception as e:
                if fresh_client is not None:
                    try:
                        await fresh_client.close()
                    except Exception as cleanup_error:
                        log_warn(f"AFC media: could not close retry session: {cleanup_error}")
                locked = is_device_lock_required_error(e)
                if not (locked or is_connection_error(e)):
                    # a real rejection (bad service name, protocol error) --
                    # retrying would just burn the wait
                    raise
                last_error = e
                reconnect = reconnect or is_connection_error(e)
                if locked and not announced:
                    announced = True
                    log_warn("AFC media restore: the device is locked - waiting "
                             "for it to be unlocked")
                    _log(OperationStatus("Your iPhone is locked. Unlock it and enter its passcode to continue restoring your photos and videos.", "authentication"))
                elif not locked:
                    log_warn(f"AFC media restore: {type(e).__name__}: {e} - retrying")
                if (time.monotonic() + delay > deadline
                        or attempt >= _AFC_OPEN_MAX_ATTEMPTS):
                    break
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, _AFC_OPEN_MAX_DELAY)
                continue
            if announced:
                _log(OperationStatus("Connected. Continuing the photo and video transfer…", "transfer_ready"))
            try:
                yield service
            finally:
                try:
                    await afc.__aexit__(None, None, None)
                finally:
                    if fresh_client is not None:
                        await fresh_client.close()
            return

        # wait budget spent: offer Abort/Resume instead of killing the restore
        err = NuggetException(
            f"Could not open the AFC service for the photo restore within "
            f"{int(timeout // 60)} min - the device stayed locked or "
            f"unreachable. Last error: {last_error}"
        )
        if prompt_choice is None or unlock_prompt is None:
            raise err from last_error
        title, text = unlock_prompt
        log_info("AFC media wait timed out; asking the user whether to resume or abort")
        try:
            decision = prompt_choice(title, text)
        except Exception as e:
            log_warn(f"AFC media prompt failed ({e}) - aborting")
            raise err from last_error
        if decision != "resume":
            raise err from last_error
        log_info("User chose to resume - restarting the AFC media wait cycle")


async def _ensure_media_directory(afc, directory, confirmed, progress_callback):
    if directory in ("", "/") or directory in confirmed:
        return
    await _ensure_media_directory(afc, posixpath.dirname(directory), confirmed, progress_callback)
    for attempt in range(6):
        try:
            try:
                present = await afc.isdir(directory)
            except AfcFileNotFoundError:
                present = False
            else:
                if not present:
                    raise NuggetException(f"AFC media: {directory} exists but is not a directory")
            if not present:
                try:
                    await afc.makedirs(directory)
                except AfcException as creation_error:
                    # Photos may create the folder between the stat and MAKE_DIR.
                    try:
                        present = await afc.isdir(directory)
                    except AfcException:
                        present = False
                    if not present:
                        raise creation_error
                if not await afc.isdir(directory):
                    raise NuggetException(f"AFC media: could not confirm directory {directory}")
            confirmed.add(directory)
            return
        except AfcException as error:
            if error.status != AfcError.PERM_DENIED:
                raise
            if attempt == 5:
                raise NuggetException(
                    f"AFC media: the device denied access to {directory}. "
                    "Photo restoration is incomplete. Keep the local media backup; "
                    "unlock the device and check the application log before resuming."
                ) from error
            progress_callback("The device denied access to the photo folder. Retrying photo restoration…")
            await asyncio.sleep(min(2 ** attempt, 5))


@asynccontextmanager
async def _pausable_media_connection(lockdown_client, progress_callback, prompt_choice, unlock_prompt):
    from src.restore.pause_control import current_pause_control
    control = current_pause_control.get()
    async with AsyncExitStack() as stack:
        async def connect(refresh=False):
            return await stack.enter_async_context(open_afc_for_media(
                lockdown_client, progress_callback=progress_callback,
                prompt_choice=prompt_choice, unlock_prompt=unlock_prompt,
                refresh_client=refresh))
        service = await connect()
        if control:
            control.state = "available"
        async def checkpoint(refresh=False):
            nonlocal service
            if refresh:
                await stack.aclose()
                service = await connect(refresh=True)
            if control and control.requested.is_set():
                await stack.aclose()
                progress_callback("Photo and video restoration paused. Keep your device connected. Select Resume to continue.")
                await control.wait_for_resume()
                service = await connect()
                control.state = "available"
                progress_callback("Resuming photo and video restoration…")
            return service
        try:
            yield checkpoint
        finally:
            if control:
                control.finish_media()


async def _wait_for_media_directory(checkpoint, directory, confirmed,
                                    progress_callback, prompt_choice):
    deadline = time.monotonic() + _AFC_OPEN_TIMEOUT
    while True:
        afc = await checkpoint()
        try:
            await _ensure_media_directory(afc, directory, confirmed, progress_callback)
            return afc
        except (AfcException, NuggetException) as error:
            cause = error.__cause__ if isinstance(error, NuggetException) else error
            if not isinstance(cause, AfcException) or cause.status != AfcError.PERM_DENIED:
                raise
            log_warn(f"AFC media: access denied to {directory}; waiting on a fresh session")
            progress_callback(OperationStatus(
                "iOS is denying access to the photo folder. Unlock your device and keep it connected. Waiting to retry…",
                "authentication"))
            if time.monotonic() >= deadline:
                message = (
                    f"iOS is still denying access to {directory}. Photo restoration is incomplete. "
                    "The local media backup has been kept. Unlock your device before resuming. "
                    "If this continues while unlocked, a service or permission problem may need to be resolved. "
                    "Resume retries photo-folder access; it does not repeat the device wipe.")
                if prompt_choice is None or prompt_choice(
                        "Photo folder access denied", message) != "resume":
                    raise NuggetException(message) from error
                deadline = time.monotonic() + _AFC_OPEN_TIMEOUT
            await asyncio.sleep(_AFC_OPEN_MAX_DELAY)
            await checkpoint(refresh=True)


async def restore_media_via_afc(lockdown_client, media_root: str,
                                progress_callback=None,
                                on_error: str = "raise",
                                prompt_choice=None,
                                unlock_prompt=None) -> dict:
    """Push a previously pulled Media tree back to the device over AFC.

    Mirrors ``media_root`` (which holds the AFC root layout: DCIM/, PhotoData/,
    ...) back onto the device after the iOS 27 security-recovery wipe. Returns
    a tally dict ``{"files": int, "bytes": int}``.

    The device has just rebooted, so the AFC open waits out a locked screen
    first (see ``open_afc_for_media``) -- pass ``prompt_choice`` to get the
    Abort/Resume prompt if that wait runs out.
    """
    root = os.path.abspath(media_root)
    if not os.path.isdir(root):
        raise NuggetException(f"AFC media store is missing ({root})")

    def _log(value):
        if progress_callback is not None and not isinstance(value, (int, float)):
            progress_callback(value)

    try:
        inventory = _media_inventory(root)
    except (OSError, ValueError) as e:
        raise NuggetException(f"Cannot read AFC media store ({root}): {e}") from e
    entries = [(os.path.join(root, *rel.split('/')), rel) for rel in sorted(inventory)]
    total_bytes = sum(inventory.values())
    if not entries:
        raise NuggetException(f"AFC media store has no photo/video payloads ({root})")

    async with _pausable_media_connection(lockdown_client, _log, prompt_choice, unlock_prompt) as checkpoint:
        done_files = 0
        done_bytes = 0
        failed: list[str] = []
        made_dirs: set = set()
        for src, rel in entries:
            afc = await checkpoint()
            remote = f"/{rel}"
            rdir = posixpath.dirname(remote)
            n = 0
            try:
                afc = await _wait_for_media_directory(
                    checkpoint, rdir, made_dirs, _log, prompt_choice)
                n = await _push_one(afc, src, remote)
            except Exception as e:
                msg = f"AFC media: failed to restore {remote}: {e}"
                if on_error == "warn":
                    log_warn(msg)
                    failed.append(remote)
                else:
                    raise NuggetException(msg) from e
            done_files += 1
            done_bytes += n
            if done_files % 25 == 0 or done_files == len(entries):
                _log(_progress_str("Restoring photos/videos over AFC",
                                   done_files, len(entries), done_bytes, total_bytes))

        log_info(f"AFC media restore complete: {done_files} files, "
                 f"{done_bytes / (1024 * 1024):.1f} MB")
        if failed:
            log_warn(f"AFC media restore: {len(failed)} files failed "
                     f"(e.g. {failed[:3]})")
            tally = {"files": done_files, "bytes": done_bytes, "failed": failed}
            return tally
    return {"files": done_files, "bytes": done_bytes}
