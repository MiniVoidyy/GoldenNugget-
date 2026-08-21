# GoldenNugget Async Operations

This document describes the background threads, async backup/restore operations, and error handling used in GoldenNugget.

## Thread Workers (src/gui/thread_workers/)

### PBDBThread
**File**: `src/gui/thread_workers/pb_worker.py`
- **Purpose**: Generic background thread for backup-driven operations (PosterBoard database, etc.)
- **Signals**: `progress` (float), `infoLbl` (str), `finished`
- Used by the PosterBoard "Fetch Database File" wizard

## Apply / Reset Flow (src/devicemanagement/device_manager.py)

### `_apply_changes()`
Main entry point for applying tweaks. Order:
1. `_raise_if_unsupported()` — hard-block iOS < 26.2
2. `_get_lockdown_values()` — device lockdown values for templating
3. `_backup_posterboard_database(force=True)` — fresh copy of the PosterBoard DB (skipped if `GOLDENNUGGET_SKIP_PB_BACKUP=1`)
4. `_apply_tweak_pass()` — generate all tweak files, handle backup encryption, then `start_restore()`

### `_apply_tweak_pass()`
- Generates every tweak's files in a single pass and restores them together
- iOS 27+: prompts for backup password if encryption is enabled (`use_encrypted_backup` pref)
- Writes `FileLocation.globalPreferencesHomeDomain` copy merged with the device's current `.GlobalPreferences.plist` so user region/language/appearance survive the iOS 27 wipe
- Calls `start_restore()` internally

### `start_restore()`
- Entry point for all restores (apply and reset)
- Opens a lockdown connection and delegates to `restore_files()`
- Passes `backup_password` for encrypted backups

### `_reset_tweaks()`
- Reset flow: `_raise_if_unsupported()` → `_capture_original_plists()` (via `psysbackup()`) → build reset files → `start_restore()`

## Restore Module (src/restore/)

### `restore_files()`
- Main restore orchestration
- Builds a `backup.Backup` object from the `FileToRestore` list
- Always delegates to `_restore_ios27()` (three-phase) — all supported devices (26.2+) go through this path

### `_restore_ios27()` — Three-Phase Restore
**Phase 1 (0-40%)**: Protective Backup
- `perform_protective_backup()` — selective backup of photos, Apple ID, settings
- `clean_backup_for_restore()` — prunes manifest to protective files only
- Injects HomeDomain/SystemPreferencesDomain tweak files into the pruned backup

**Phase 2 (40-60%)**: Sparse Restore + Reboot
- `perform_restore()` — applies tweaks via sparse restore
- Triggers the iOS 27 "safe state recovery" wipe on reboot

**Phase 3 (60-100%)**: Protective Restore
- `_wait_for_device()` — reconnects after reboot (20 min timeout)
- `_restore_protective_backup()` — restores the Phase 1 backup, with password if encrypted

### `perform_protective_backup()` (src/restore/protective.py)
- Creates a selective device backup via mobilebackup2
- Filters: keeps HomeDomain (Accounts, ConfigurationProfiles, Preferences, SpringBoard, ControlCenter), CameraRoll/Media (photos)
- Skips: AppDomain-* containers (empty `Applications` in factory info), KeychainDomain
- Encryption: uses existing encryption if enabled, otherwise unencrypted
- Retry logic: 3 attempts, backoff `min(2**attempt, 15)`s (2s, 4s) for connection errors

### `clean_backup_for_restore()` (src/restore/protective.py)
- Prunes Manifest.db to protective files only (temp-table keep-set, single DELETE)
- Removes orphaned payload files
- Skipped for encrypted backups (device handles it)

### `_restore_protective_backup()` (src/restore/restore.py)
- Restores the pruned backup after the security recovery
- Retries up to 12 times, fixed 10s between attempts (SpringBoard/mobilebackup2 startup delay)
- Accepts `backup_password` for encrypted backups

## Original Plist Capture (src/restore/original_plist.py)

### `psysbackup()`
- Full device backup to capture original plists before a reset
- Templates device-specific values (SerialNumber, DeviceName, etc.)
- Skipped if backup encryption is enabled
- Retry logic: 3 attempts, backoff `min(2**attempt, 15)`s (2s, 4s) for connection errors
- Validates Manifest.db is valid SQLite before reading

## PosterBoard Backup (src/gui/dialogs/pb_dialog.py)

### `backup_posterboard_database()`
- Backs up the PosterBoard SQLite database for animated wallpapers
- Uses incremental backup if a previous backup exists
- Retry logic: 3 attempts, backoff `min(2**attempt, 15)`s (2s, 4s) for connection errors
- Validates Manifest.db before extracting the database

## Error Handling

### Device Lock Detection
- `_is_device_locked_error()` — detects ErrorCode 208 (MBErrorDomain/208)
- Defined in `device_manager.py`, `protective.py`, `original_plist.py`, `pb_dialog.py`
- Used in: `psysbackup()`, `backup_posterboard_database()`, `perform_protective_backup()`, `_backup_posterboard_database()`, `_capture_original_plists()`
- User message: "Device locked - unlock and keep awake"

### Connection Error Detection
- `_is_connection_error()` — detects ConnectionTerminatedError, IncompleteReadError, ConnectionError, OSError, asyncio.TimeoutError
- Retry logic: 3 attempts with backoff `min(2**attempt, 15)`s — actual delays are 2s and 4s
- Used in all backup/restore operations

### Backup Encryption Handling
- Checks `get_will_encrypt()` before operations
- iOS 27+ apply: prompts for password via QInputDialog if encryption is enabled and `use_encrypted_backup` is set
- Phase 3 passes the password to `mb.restore(password=backup_password)`
- `psysbackup` capture is skipped if encrypted (cannot read manifest)

## Async/Await Patterns

All device communication uses async/await with pymobiledevice3:
- `create_using_usbmux()` — Lockdown connection
- `Mobilebackup2Service` — Backup/restore operations
- `AfcService` — File system access
- `InstallationProxyService` — App info
- `MobileConfigService` — Profile management

## Progress Reporting

Progress callbacks pass through the call chain:
```
update_label (UI)
  → _backup_progress() / progress_callback
  → psysbackup() / perform_protective_backup() / backup_posterboard_database()
  → mb.backup() / mb.restore() progress callbacks
```

## Key Retry Configurations

| Operation | Max Retries | Backoff | Errors Handled |
|-----------|-------------|---------|----------------|
| Protective Backup | 3 | 2s, 4s | Connection, Device Locked |
| psysbackup (pre-reset capture) | 3 | 2s, 4s | Connection, Device Locked |
| PosterBoard Backup | 3 | 2s, 4s | Connection, Device Locked |
| Phase 3 Restore | 12 | 10s fixed | Transient (service not ready) |

## Data Flow Summary

```
User clicks "Apply Tweaks"
    |
_apply_changes()
    |_ _raise_if_unsupported()
    |_ _get_lockdown_values()
    |_ _backup_posterboard_database(force=True)   [skip: GOLDENNUGGET_SKIP_PB_BACKUP=1]
    |_ _apply_tweak_pass()
         |_ generate tweak files
         |_ backup encryption handling (iOS 27+ password prompt)
         |_ start_restore()
              |_ restore_files()
                   |_ _restore_ios27()
                        Phase 1: perform_protective_backup() + clean_backup_for_restore() + inject tweaks
                        Phase 2: perform_restore() (sparse) -> reboot
                        Phase 3: _wait_for_device() -> _restore_protective_backup(password)
```

## Logging

- Console output: `print()` for immediate feedback
- Log file: `/tmp/goldennugget_log.txt` (via `src/restore/protective.py` log functions)
- Verbose logging: pass `--debug` to `main_app.py`; log file path can be overridden with the `GOLDENNUGGET_LOG_FILE` env var