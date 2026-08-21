# GoldenNugget 9.0 beta 1

First beta of the 9.0 line, timed for the iOS 27 release.
**Tested on iOS 27 developer beta 6 / public beta 4.**

## Highlights

### Smart Backup Cache (the headline)
Applying tweaks no longer re-uploads your whole protective data every time:

- A per-device **master backup cache** lives in the system temp dir
  (`/tmp/goldennugget_protective_cache`). The first apply makes a full
  selective backup; every next apply runs a true **incremental refresh** —
  only what changed on the device is uploaded.
- Non-protective payloads are drained mid-stream during the backup itself,
  so no multi-GB temporary files ever hit the disk.
- Phase 3 restores from an instant hardlink working copy — pruning and tweak
  injection never touch the cached master.
- Measured on dev beta 6: **full apply cycle ≈ 95 seconds**
  (backup → tweaks → reboot → data restore).

### PosterBoard inside the protective backup
- The PosterBoard container rides the same backup session; its database is
  extracted right after the incremental refresh, so wallpaper tweaks always
  build on the live on-device state. **One mobilebackup2 session per apply**
  instead of two full backups.
- The database is resolved by file name (structure version 61/62/... varies
  between iOS releases) and WAL-checkpointed into a single consolidated file.

### Reliability work
- Prune self-heal: manifest rows without payloads are dropped before they can
  abort Phase 3 (MBErrorDomain/205); directory rows are preserved
  (renameatx ENOENT fix).
- Encrypted backups: supported with the user-provided password (manifest is
  decrypted locally on the working copy only). Without a password the cache
  is bypassed automatically.
- Legacy `--enable-legacy-support` flag removed; iOS < 26.2 stays hard-blocked.

### Code health (9.0 rework, part 1)
- Declarative tweak registry: one entry defines id/title/plist/compatibility/UI
  kind; loader and UI derive from it.
- `lockdown_session()` context manager replaces ad-hoc connection handling.
- Large dead-code sweep (~1.5k lines): duplicate helpers, unreachable branches,
  stale enums, debug leftovers.

## Known limitations

- **Encrypted backups**: the decrypt/prune/re-encrypt path is new — exercise
  it and report. Injected tweak payloads stay plaintext inside an otherwise
  device-encrypted backup; restore-agent behaviour for that mix is unverified.
- Status Bar remains disabled on iOS 27+ (Speakeasy gate).
- Passcode Themes removed (confirmed non-functional on iOS 27).
- Kill switch for the new cache: `GOLDENNUGGET_NO_BACKUP_CACHE=1`.
