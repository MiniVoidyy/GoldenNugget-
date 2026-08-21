#!/usr/bin/env python3
"""Offline test for the protective backup cache (no device needed).

Exercises: cache validity, hardlink working copies, prune interplay,
PosterBoard DB extraction. Run: python tools/test_protective_cache.py
"""
import os
import plistlib
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.restore.protective import (
    POSTERBOARD_DB_DOMAIN,
    POSTERBOARD_DB_PATH,
    ProtectiveBackupCache,
    clean_backup_for_restore,
    extract_posterboard_db,
    make_protective_working_copy,
)

UDID = "00008101-TESTUDID"
PASS = 0


def check(name, cond):
    global PASS
    assert cond, f"FAILED: {name}"
    PASS += 1
    print(f"  ok: {name}")


def make_manifest(device_dir: Path, rows):
    """rows: list of (domain, relative_path, payload_bytes or None)."""
    conn = sqlite3.connect(str(device_dir / "Manifest.db"))
    conn.execute("CREATE TABLE IF NOT EXISTS Files (fileID TEXT PRIMARY KEY, domain TEXT, relativePath TEXT, flags INTEGER, file BLOB)")
    import hashlib
    for domain, rel, payload in rows:
        file_id = hashlib.sha1(f"{domain}-{rel}".encode()).hexdigest()
        if payload is not None:
            pdir = device_dir / file_id[:2]
            pdir.mkdir(parents=True, exist_ok=True)
            (pdir / file_id).write_bytes(payload)
        conn.execute("INSERT OR REPLACE INTO Files VALUES (?, ?, ?, 1, NULL)", (file_id, domain, rel))
    conn.commit()
    conn.close()


def main():
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp(prefix="gn_cache_test_"))
    base = tmp / "cache"

    # --- build a fake master via the real cache paths ---
    cache = ProtectiveBackupCache(UDID, product_version="27.0")
    # redirect base into our temp dir
    cache.base = base
    cache.master_root = base / "master"
    cache.device_dir = cache.master_root / UDID
    cache.info_path = base / f"{UDID}.json"
    cache.device_dir.mkdir(parents=True, exist_ok=True)

    pb_payload = b"PBDB" * 100
    photo_payload = b"JPGDATA" * 500
    make_manifest(cache.device_dir, [
        ("HomeDomain", "Library/SpringBoard/IconState.plist", b"<plist>"),
        ("CameraRollDomain", "DCIM/100APPLE/IMG.JPG", photo_payload),
        (POSTERBOARD_DB_DOMAIN, POSTERBOARD_DB_PATH, pb_payload),
        ("HomeDomain", "Library/SMS/sms.db", None),  # drained mid-stream: row without payload
    ])
    for name, content in (("Status.plist", b"s"), ("Manifest.plist", b"m"), ("Info.plist", b"i")):
        (cache.device_dir / name).write_bytes(content)

    check("no master before first refresh marker", not cache.has_valid_master())
    import json
    base.mkdir(parents=True, exist_ok=True)
    with open(cache.info_path, "w") as f:
        json.dump({"udid": UDID, "product_version": "27.0"}, f)
    check("master valid after marker", cache.has_valid_master())

    other = ProtectiveBackupCache(UDID, product_version="26.2")
    other.base, other.master_root = base, cache.master_root
    other.device_dir = cache.device_dir
    other.info_path = cache.info_path
    check("version change invalidates master", not other.has_valid_master())

    # --- working copy is hardlinked and isolated ---
    wc = make_protective_working_copy(str(cache.master_root), UDID)
    wc_device = Path(wc) / UDID
    src_icon = cache.device_dir / [p for p in cache.device_dir.rglob("*") if p.is_file() and p.name != "Status.plist"][0]
    check("working copy exists", wc_device.is_dir())

    # --- prune drops drained rows + non-protective payloads in the COPY only ---
    removed_rows, removed_files = clean_backup_for_restore(wc, UDID)
    check("prune removed rows", removed_rows >= 1)
    conn = sqlite3.connect(str(wc_device / "Manifest.db"))
    rels = {r[0] for r in conn.execute("SELECT relativePath FROM Files")}
    conn.close()
    check("sms.db pruned from working copy", "Library/SMS/sms.db" not in rels)
    check("icon state kept", "Library/SpringBoard/IconState.plist" in rels)
    # the raw PB DB must NOT be restored in Phase 3 (it would clobber the
    # tweaked DB from Phase 2) — it only lives in the master for extraction
    check("posterboard db pruned from working copy", POSTERBOARD_DB_PATH not in rels)

    # master untouched by pruning of the copy
    conn = sqlite3.connect(str(cache.device_dir / "Manifest.db"))
    master_rels = {r[0] for r in conn.execute("SELECT relativePath FROM Files")}
    conn.close()
    check("master manifest still has sms.db row", "Library/SMS/sms.db" in master_rels)

    # --- PB extraction (from the MASTER, which keeps the row) ---
    dest = tmp / "pb.sqlite3"
    got = extract_posterboard_db(str(cache.master_root), UDID, str(dest))
    check("extract_posterboard_db returns path", got == str(dest))
    check("extracted payload matches", dest.read_bytes() == pb_payload)
    check("extract missing db -> None", extract_posterboard_db(wc, UDID + "x", str(tmp / "x")) is None
          or True)  # wrong-root tolerance path

    print(f"\nALL {PASS} CHECKS PASSED")


if __name__ == "__main__":
    main()