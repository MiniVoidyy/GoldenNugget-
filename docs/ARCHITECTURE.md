# GoldenNugget Architecture

A guided tour of every part of the codebase: what each package does, how the
main flows work end-to-end, and which conventions hold the whole thing
together. For agent-facing operational notes see [AGENTS.md](../AGENTS.md);
for the iOS 27 status-bar research see [iOS27_StatusBar_Research.md](iOS27_StatusBar_Research.md).

```
main_app.py ──► src/gui/main_window.py ──► pages/ (classic UI)  +  ios/ (iOS-style UI)
                        │
                        ▼
            src/devicemanagement/device_manager.py   (apply / reset orchestration)
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
  src/tweaks/     src/restore/      src/controllers/
  (what to write) (how to write it) (helpers: plists, xml, presets, …)
```

---

## Entry point — `main_app.py`

1. Adds `src/qt` to `sys.path` so the generated resource modules import.
2. CLI dispatcher: `python main_app.py -m <script>` runs a tool module;
   `--test-mode` creates a mock device (no USB needed); `--debug` enables
   verbose logging; `GOLDENNUGGET_LOG_FILE` overrides the log path.
3. Creates `QApplication`, installs the `Translator`, builds `MainWindow`,
   `DeviceManager` and the global `tweaks` registry.

Build: `compile.py` wraps PyInstaller (`Nugget.spec`, `version.txt` for
Windows metadata, icons, i18n resources).

## Global state — three singletons

| Object | File | Purpose |
|---|---|---|
| `tweaks` | `src/tweaks/tweaks.py` | `dict[TweakID → Tweak instance]`; the single source of runtime tweak state both UIs read and write |
| `DeviceManager` | `src/devicemanagement/device_manager.py` | device discovery, apply/reset orchestration |
| `DataSingleton` | `src/devicemanagement/data_singleton.py` | `current_device` + `device_available` shared across UI layers |

---

## src/devicemanagement/ — talking to the device

### `session.py`
`lockdown_session(serial)` — the **only** sanctioned way to open a lockdown
connection. Async context manager that always closes safely (a rebooted
device makes `close()` raise `ConnectionTerminatedError`, which must never
mask the real result). `create_using_usbmux` appears directly only where
connection ownership transfers to a caller (`_wait_for_device`,
`perform_restore`).

### `constants.py`
- `Device` — plain data object (udid, version, model, locale…).
- `is_supported_by_fork(version)` — hard gate: iOS > 26.1 only.
- `Version` — re-export of `packaging.version.Version`.

### `preference_manager.py`
QSettings-backed user preferences (`auto_reboot`, `use_encrypted_backup`,
skip-setup options…) plus the PosterBoard saved-database helpers.

### `device_manager.py` — the orchestrator
Key methods:

- `_get_devices()` — usbmux scan; per-device lockdown probe; encryption check
  (blocks non-experimental encrypted use); builds `Device` objects.
- `apply_changes()` → `_apply_changes()` — the main flow, see below.
- `_prepare_protective_backup()` — Phase 0: cached protective backup; when
  wallpapers are applied, also includes the PosterBoard container and
  extracts its database right after the refresh. Returns a `PreparedBackup`.
- `_apply_tweak_pass()` — asks every loaded tweak to generate its files,
  merges them into one restore list, handles backup-encryption prompts,
  then calls `start_restore()`.
- `start_restore()` → `restore_files()` (src/restore).
- `reset_tweaks()` — captures original plists via `psysbackup()`, then builds
  "restore the originals" files per selected page.

#### Apply flow (end-to-end)
```
apply_changes()
 ├─ _raise_if_unsupported()                    iOS < 26.2 hard-blocked
 ├─ _prepare_protective_backup()               Phase 0 (cache, see below)
 │    ├─ encrypted? prompt password / bypass cache
 │    └─ wallpapers applied? include PB container + extract DB after refresh
 ├─ _backup_posterboard_database(force=True)   only if the cache could not
 │                                             provide a usable DB
 └─ _apply_tweak_pass(prepared_backup_root)
      ├─ every tweak.apply_tweak(...)          files generated into one list
      ├─ skip-setup + .GlobalPreferences copy  HomeDomain survival copies
      ├─ backup-encryption password handling   (iOS 27+)
      └─ start_restore(files, prepared_backup_root)
           └─ restore_files → _restore_ios27   three phases, below
```

---

## src/tweaks/ — what gets written

### Registry-first design (`registry.py`)
Every plist-based tweak is defined **once** as a `TweakSpec`:
id, section (Liquid Glass / SpringBoard / Internal), title (marked with
`QT_TRANSLATE_NOOP` — translated at render time), plist location, key,
default value, UI kind (`switch` / `text` / `number`), compatibility
(`min_version`, `iphone_only`, `ipad_only`) and an optional `factory` for
non-basic tweaks (e.g. the AdvancedPlistTweak behind WatchOS Compatibility).

Consumers:
- `tweak_loader.load_plist_tweaks()` builds instances into `tweaks`
  (the classic `load_internal/load_liquidglass/load_springboard` names remain
  as aliases; Daemons stay hand-defined there).
- The iOS tweaks page renders sections straight from `SPECS_BY_SECTION`.
- `gui/ios/compat.py` evaluates `min_version` / device restrictions from the
  spec (public API unchanged).

Adding a tweak = adding one registry entry.

### Tweak classes (`tweak_classes.py`)
`Tweak` base (enabled/value/change-notification) with concrete generators:
- `BasicPlistTweak` — one key into one managed plist.
- `AdvancedPlistTweak` — a dict of keys into one plist.
- `NullifyFileTweak` — writes an empty file (plist nuking).
- `StatusBarTweak`, `PasscodeThemeTweak`… — special generators.

`Daemons` is an AdvancedPlistTweak over `Daemon` enum values
(`src/tweaks/daemons_tweak.py`); disabling the Location Services daemon on an
iPhone 14 triggers a wallpaper-risk warning in both UIs.

### PosterBoard subsystem (`tweaks/posterboard/`)
Wallpapers are always applied **as configurations written into the
PosterBoard sqlite database** (the old descriptor-file method was removed —
broken on iOS 26+).

- `posterboard_tweak.py` — extracts tendies/templates into a temp dir,
  walks them (`recursive_add`), registers configuration entries, stages the
  modified DB and appends it as an AppDomain file; optional live-photo /
  video-loop CAML generation (`video_handler`).
- `pb_config_manager.py` — the DB pipeline: pulls the live DB (from the
  protective-backup cache), validates (WAL-consolidated, schema-relaxed for
  db5+), stages config entries, produces the modified database.
- `template_file.py` + `template_options/` — the `.batter`-style template
  format: JSON-defined option widgets (picker/remove/replace/set) that edit
  caml/xml/plist payloads at apply time.
- `status_bar/status_setter.py` + `status_bar_tweak.py` — binary
  `StatusBarOverrideData` struct (cffi) translated into the Speakeasy
  FeatureFlags payload; disabled on iOS 27+ (no write permission).

---

## src/restore/ — how it gets written

### `restore.py` — three-phase restore (`_restore_ios27`)
All supported devices (26.2+) take this path:

```
Phase 0 (in device_manager): cached protective backup + PosterBoard DB
Phase 1 (0-40%):  working copy of the cached master (hardlinks)
                  → clean_backup_for_restore() prune
                  → inject HomeDomain/SystemPreferencesDomain tweak files
Phase 2 (40-60%): perform_restore() sparse restore → reboot
                  → iOS 27 "safe state recovery" wipes data volume
Phase 3 (60-100%): _wait_for_device() (20 min budget)
                  → _restore_protective_backup() puts user data back
```

`prepared_backup_root` is a `PreparedBackup(root, manifest_password)`; when
absent (encrypted-without-password / kill switch), Phase 1 falls back to an
in-place `perform_protective_backup()`.

Sparse staging itself lives in `backup.py` + `mbdb.py` (MBDB/Manifest
construction) and `__init__.py::perform_restore`.

### `protective.py` — the cache and everything around it
- `ProtectiveBackupCache` — per-device master copy in
  `<temp>/goldennugget_protective_cache/master/<udid>`. The master keeps a
  FULL Manifest.db (rows for drained payloads stay) so mobilebackup2 can run
  true incremental refreshes; invalidated by UDID/iOS-version change or by
  the encryption state flipping; a reboot wipes it naturally.
- `perform_protective_backup(..., incremental_ok)` — selective backup:
  pymobiledevice3's native `filter_callback` drains non-protective uploads
  mid-stream while their manifest rows survive (that is what makes the next
  incremental cheap). Keep-set: CameraRoll/Media (photos),
  SystemPreferencesDomain, HomeDomain Accounts / ConfigurationProfiles /
  Preferences / SpringBoard / ControlCenter, optionally the PosterBoard DB.
- `make_protective_working_copy()` — hardlink clone (metadata real-copied);
  pruning never corrupts the master.
- `clean_backup_for_restore()` — prunes to the keep-set; self-heals by
  dropping regular-file rows whose payload is missing (MBErrorDomain/205)
  while keeping directory rows (renameatx ENOENT). Encrypted manifests are
  decrypted/pruned/re-encrypted locally via pymobiledevice3 when a password
  is supplied.
- `inject_file_into_backup()` — adds fresh tweak content (incl. directory
  rows, donor MBFile blobs, unique inodes) so injected tweaks survive the
  wipe through Phase 3's native restore.
- `extract_posterboard_db()` — resolves the PB database by FILE NAME
  (structure version varies), pulls `-wal`/`-shm` siblings and checkpoints
  them into one consolidated database.
- `verify_backup_payloads()` — last-line diagnostic before Phase 3.
- `check_disk_space_for_backup()` — sizes the requirement from the device's
  real used storage; `GOLDENNUGGET_MIN_FREE_GB` overrides the floor.

### `original_plist.py`
`psysbackup()` — full capture of the plists listed by `FileLocation` so
Reset can restore originals instead of empty files; skipped when backup
encryption is on.

---

## src/gui/ — two UIs, one state

- **Classic** — Qt Designer stack (`mainwindow.ui` → `mainwindow_ui.py`),
  page wrappers in `pages/main/*` and `pages/tools/*`, registered in
  `pages_list.py` (`Page` enum doubles as the QStackedWidget index).
- **iOS-style** — hand-built widget pages in `ios/` (`home`, `tweaks`,
  `posterboard`, `daemons`, `settings`, `statusbar`), rendered from the
  registry where applicable.
- Both bind to the same `tweaks` instances — toggling in either UI changes
  the same state; `theme_manager.py` switches between visual themes.
- Dialogs: PosterBoard fetch wizard (`pb_dialog.py`), reset picker
  (`reset_dialog.py`), about/update/help (`dialogs.py`).
- Thread workers (`thread_workers/`): `PBDBThread` runs backup functions off
  the UI thread; `ApplyThread`/`RefreshDevicesThread` wrap asyncio entry
  points and surface alerts.

## src/controllers/ — support services

| Module | Role |
|---|---|
| `settings.py` | QSettings with org-name migration |
| `preset_manager.py` | export/import/apply of tweak presets (per-tweak serializers) |
| `translator.py` | language switching (+ RTL fixes), `.ts/.qm` pipeline via pyside6-lupdate/lrelease |
| `plist_handler.py` / `xml_handler.py` | plist key writes; XML/caml value setters (hardened eval) |
| `video_handler.py` | ffmpeg-based video→CAML conversion for video wallpapers |
| `files_handler.py` / `path_handler.py` | bundled-resource access, Windows path fixes |
| `web_request_handler.py` | update checks |

## Conventions

- **Errors**: `NuggetException` for user-facing failures; connection/locked
  error classification lives in `src/exceptions/device_errors.py` and feeds
  uniform retry loops (`min(2**attempt, 15)s`; Phase 3 uses fixed 10 s × 12).
- **Logging**: `log_info/log_warn/log_error` in `protective.py` → console +
  `/tmp/goldennugget_log.txt` (`GOLDENNUGGET_LOG_FILE` overrides).
- **i18n**: all UI strings go through `QCoreApplication.translate("Nugget", …)`
  (or `QT_TRANSLATE_NOOP` in data modules); catalogs are crowdsourced in the
  gNugget-i18n submodule and synced by CI.
- **Kill switches**: `GOLDENNUGGET_NO_BACKUP_CACHE`,
  `GOLDENNUGGET_SKIP_PB_BACKUP`, `GOLDENNUGGET_MIN_FREE_GB`.
- **Testing**: offline regression for the backup cache in
  `tools/test_protective_cache.py` (no device needed); smoke run =
  `QT_QPA_PLATFORM=offscreen python main_app.py --test-mode`.
