import faulthandler, os, sys, json, time, shutil, sqlite3
faulthandler.dump_traceback_later(15, exit=True)
sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'qt'))
sys.path.insert(0, os.getcwd())
os.environ["GOLDENNUGGET_CACHE_PERSIST_MIN_GB"] = "0"  # force persistent placement
from pathlib import Path
from src.restore.protective import ProtectiveBackupCache, CACHE_PERSIST_MIN_GB

UDID = "UDIDPLC"; tmp = Path(os.getcwd()) / "_cache_plc_test"
shutil.rmtree(tmp, ignore_errors=True)
cache = ProtectiveBackupCache(UDID, "27.0")
cache._temp_base = tmp / "temp_base"
cache._persist_base = tmp / "persist_base"
cache.base = cache._temp_base
cache.master_root = cache._temp_base / "master"
cache.device_dir = cache.master_root / UDID
cache.info_path = cache._temp_base / f"{UDID}.json"

dev = cache.device_dir; dev.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(dev / "Manifest.db"); conn.execute("CREATE TABLE Files (x)")
conn.commit(); conn.close()
for n in ("Manifest.plist", "Status.plist"): (dev / n).write_bytes(b"x" * 300)
open(dev / "big_payload.bin", "wb").write(b"\0" * (2 * 1024 * 1024))  # 2 MB payload
(cache._temp_base / f"{UDID}.json").write_text(json.dumps({
    "udid": UDID, "product_version": "27.0", "encrypted": False,
    "created_ts": int(time.time())}))
P = lambda *a: print(*a, flush=True)
P("threshold GB:", CACHE_PERSIST_MIN_GB)

assert cache.locate() is not None, "locate failed before relocation"
old_home = str(cache.base)
cache.relocate_by_size()
assert cache.base == cache._persist_base, f"not relocated: {cache.base}"
assert (cache._persist_base / "master" / UDID / "Manifest.db").is_file()
assert not (cache._temp_base / "master").exists(), "old tree left behind"
P("relocated to persistent base")

cache._set_home(cache._persist_base)
assert cache.locate() is not None and str(cache.base) == str(cache._persist_base)
P("locate follows the persistent home")

info = json.loads((cache._persist_base / f"{UDID}.json").read_text())
info["created_ts"] = int(time.time()) - 3600
(cache._persist_base / f"{UDID}.json").write_text(json.dumps(info))
res = cache.locate()
assert res["age_secs"] >= 3500
P("age_secs honours created_ts:", res["age_secs"])

shutil.rmtree(tmp, ignore_errors=True)
print("ALL PLACEMENT CHECKS PASSED", flush=True)
