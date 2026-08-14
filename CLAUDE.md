# CLAUDE.md - GoldenNugget Development Guide

## Project Overview
GoldenNugget is an iOS customization tool for iOS 26.2-27.0+ that applies tweaks via a three-phase backup→tweak→restore workflow. Uses Python 3.9+, PySide6, and pymobiledevice3.

## Key Architecture

### Three-Phase Restore (iOS 27+)
```
Phase 1: Protective Backup (photos, Apple ID, settings)
Phase 2: Sparse Restore + Reboot (triggers security wipe)
Phase 3: Protective Restore (restores user data after wipe)
```

### Main Entry Points
- `main_app.py` - Application entry
- `src/devicemanagement/device_manager.py` - Core device operations
- `src/restore/restore.py` - Restore orchestration
- `src/restore/protective.py` - Protective backup logic

## Critical Files

| File | Purpose |
|------|---------|
| `src/devicemanagement/device_manager.py` | Device management, tweak application |
| `src/restore/restore.py` | iOS 27 three-phase restore logic |
| `src/restore/protective.py` | Selective backup, encryption handling |
| `src/restore/original_plist.py` | Pre-apply snapshot (auto-revert) |
| `src/gui/dialogs/pb_dialog.py` | PosterBoard database backup |

## Error Handling Patterns

### Device Locked (ErrorCode 208)
```python
def _is_device_locked_error(exc: Exception) -> bool:
    msg = str(exc)
    return "ErrorCode" in msg and ("208" in msg or "Device locked" in msg or "MBErrorDomain" in msg)
```

### Connection Errors
```python
def _is_connection_error(exc: Exception) -> bool:
    return isinstance(exc, (ConnectionTerminatedError, ConnectionError, OSError, asyncio.TimeoutError))
```

### Retry Logic
- 3 attempts, exponential backoff (2s, 4s, 8s)
- Used in: protective backup, pre-apply snapshot, PosterBoard backup

## Backup Encryption
- Check with `mb.get_will_encrypt()`
- If enabled: prompt user for password via QInputDialog
- Phase 3 passes password to `mb.restore(password=backup_password)`
- Pre-apply snapshot skipped if encrypted

## Development Commands

```bash
# Run application
python main_app.py

# Compile UI
pyside6-uic --from-imports src/qt/mainwindow.ui -o src/qt/mainwindow_ui.py

# Compile resources
pyside6-rcc src/qt/resources.qrc -o src/qt/resources_rc.py
```

## Debug Mode
Set `gNugget_DEV_MODE=enable` for verbose logging to `/tmp/goldennugget_log.txt`

## Key Constraints
- Device MUST be unlocked and awake during backups
- Find My must be disabled for restore
- USB cable quality matters (connection drops cause failures)
- iOS 27+ requires three-phase workflow (no sparse-only)