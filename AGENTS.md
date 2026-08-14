# GoldenNugget Agents Documentation

This document describes the background agents, workers, and async tasks used in GoldenNugget.

## Thread Workers (src/gui/thread_workers/)

### PBDBThread
**File**: `src/gui/thread_workers/pb_worker.py`
- **Purpose**: Background thread for PosterBoard database operations
- **Operations**:
  - Backup PosterBoard database from device
  - Apply tendie modifications to database
  - Restore modified database to device
- **Signals**: Progress updates, completion, error reporting

## Async Backup/Restore Operations

### DeviceManager Async Methods (src/devicemanagement/device_manager.py)

#### `_apply_changes()`
- Main entry point for applying tweaks
- Coordinates: original capture → snapshot → tweak application → restore
- Runs on main event loop

#### `_snapshot_last_apply()`
- Captures pre-apply state for auto-revert functionality
- Uses `psysbackup()` to backup system plists before modification
- Skipped if backup encryption enabled (cannot read encrypted manifest)

#### `_backup_posterboard_database()`
- Backs up PosterBoard SQLite database for wallpaper modifications
- Uses `backup_posterboard_database()` from pb_dialog.py

#### `_apply_tweak_pass()`
- Generates all tweak files and restores in single pass
- On iOS 27+: Uses three-phase protective backup/restore
- On iOS 26-: Uses sparse restore per tendie

#### `start_restore()`
- Entry point for restore operations
- Handles both BookRestore (AFC) and standard restore paths
- Passes backup password for encrypted backups

### Restore Module (src/restore/)

#### `restore_files()`
- Main restore orchestration
- Creates backup object from FileToRestore list
- iOS 27+: Delegates to `_restore_ios27()` (three-phase)
- iOS 26-: Uses `perform_restore()` (sparse)

#### `_restore_ios27()` - Three-Phase Restore
**Phase 1 (0-40%)**: Protective Backup
- `perform_protective_backup()` - Selective backup of photos, Apple ID, settings
- `clean_backup_for_restore()` - Prunes manifest to protective files only
- Injects tweak files into pruned backup

**Phase 2 (40-60%)**: Sparse Restore + Reboot
- `perform_restore()` - Applies tweaks via sparse restore
- Triggers iOS 27 "safe state recovery" wipe on reboot

**Phase 3 (60-100%)**: Protective Restore
- `_wait_for_device()` - Reconnects after reboot
- `_restore_protective_backup()` - Restores Phase 1 backup with password if encrypted

#### `perform_protective_backup()` (src/restore/protective.py)
- Creates selective device backup via mobilebackup2
- Filters: keeps HomeDomain (Apple ID, prefs, SpringBoard), CameraRoll/Media (photos)
- Skips: AppDomain-* containers, KeychainDomain
- Handles encryption: uses existing if enabled, otherwise unencrypted
- Retry logic: 3 attempts with exponential backoff for connection errors

#### `clean_backup_for_restore()` (src/restore/protective.py)
- Prunes Manifest.db to protective files only
- Removes orphaned payload files
- Skipped for encrypted backups (device handles it)

#### `_restore_protective_backup()` (src/restore/restore.py)
- Restores pruned backup after security recovery
- Retries up to 12 times (SpringBoard/mobilebackup2 startup delay)
- Accepts `backup_password` for encrypted backups

### Original Plist Capture (src/restore/original_plist.py)

#### `psysbackup()`
- Full device backup to capture original plists before modification
- Templates device-specific values (SerialNumber, DeviceName, etc.)
- Skipped if backup encryption enabled
- Retry logic: 3 attempts for connection errors
- Validates Manifest.db is valid SQLite before reading

### PosterBoard Backup (src/gui/dialogs/pb_dialog.py)

#### `backup_posterboard_database()`
- Backs up PosterBoard SQLite database for animated wallpapers
- Uses incremental backup if previous backup exists
- Retry logic: 3 attempts for connection errors
- Validates Manifest.db before extracting database

## Error Handling Agents

### Device Lock Detection
- `_is_device_locked_error()` - Detects ErrorCode 208 (MBErrorDomain/208)
- Used in: `psysbackup()`, `backup_posterboard_database()`, `perform_protective_backup()`, `_snapshot_last_apply()`, `_backup_posterboard_database()`
- User message: "Device locked - unlock and keep awake"

### Connection Error Detection
- `_is_connection_error()` - Detects ConnectionTerminatedError, IncompleteReadError, etc.
- Retry logic with exponential backoff (2s, 4s, 8s)
- Used in all backup/restore operations

### Backup Encryption Handling
- Checks `get_will_encrypt()` before operations
- Prompts for password via QInputDialog if encrypted (iOS 27+)
- Phase 3 passes password to `mb.restore(password=backup_password)`
- Pre-apply snapshot skipped if encrypted (cannot read manifest)

## Async/Await Patterns

All device communication uses async/await with pymobiledevice3:
- `create_using_usbmux()` - Lockdown connection
- `Mobilebackup2Service` - Backup/restore operations
- `AfcService` - File system access
- `InstallationProxyService` - App info
- `MobileConfigService` - Profile management

## Progress Reporting

Progress callbacks passed through call chain:
```
update_label (UI) 
  → _backup_progress() / progress_callback
  → psysbackup() / perform_protective_backup() / backup_posterboard_database()
  → mb.backup() / mb.restore() progress callbacks
```

## Key Retry Configurations

| Operation | Max Retries | Backoff | Errors Handled |
|-----------|-------------|---------|----------------|
| Protective Backup | 3 | 2s, 4s, 8s | Connection, Device Locked |
| Pre-apply Snapshot | 3 | 2s, 4s, 8s | Connection, Device Locked |
| PosterBoard Backup | 3 | 2s, 4s, 8s | Connection, Device Locked |
| Phase 3 Restore | 12 | 10s fixed | Transient (service not ready) |

## Data Flow Summary

```
User clicks "Apply Tweaks"
    ��
_apply_changes()
    ��
_snapshot_last_apply() → psysbackup() → [encrypted? skip : backup + template]
    ��
_apply_tweak_pass() → generate tweak files
    ��
start_restore() → restore_files()
    ��
iOS 27+: _restore_ios27()
    Phase 1: perform_protective_backup() + clean_backup_for_restore() + inject tweaks
    Phase 2: perform_restore() (sparse) → reboot
    Phase 3: _wait_for_device() → _restore_protective_backup(password)
    ��
iOS 26-: perform_restore() (sparse)
```

## Logging

- Console output: `print()` for immediate feedback
- Log file: `/tmp/goldennugget_log.txt` (via `src/restore/protective.py` log functions)
- Debug mode: Set `gNugget_DEV_MODE=enable` env var for verbose output