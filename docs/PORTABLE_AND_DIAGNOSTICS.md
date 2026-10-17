# Portable presets, diagnostics and offline inspection

## Portable presets

On the Presets page, choose **Export** or **Partial Export**, then select
**Portable Preset with Templates and Icons (*.gnpreset)** in the save dialog.
The existing JSON format remains available. **Import** accepts either format.
Archive transfers run on a background thread.

```sh
python nugget_cli.py preset export "My Preset" --portable --out my-preset.gnpreset
python nugget_cli.py preset export "My Preset" --portable --include Templates,IconThemes
python nugget_cli.py preset import my-preset.gnpreset --name "Imported Preset"
```

The portable format includes the saved preset's template packages and icon
images. Missing assets cause an export error; an incomplete archive does not
replace a previous export. PosterBoard wallpapers remain excluded from presets
and are imported separately as `.tendies` files.

`.gnpreset` is a ZIP containing `manifest.json` and `assets/` entries. The
version 1 manifest has a `format` of `GoldenNugget portable preset`, the JSON
`preset`, and an `assets` mapping of internal filenames to `size` and `sha256`.
Asset references in the preset use `bundle://assets/...`. Import checks the
manifest, references, sizes, CRCs and SHA-256 values, then rewrites the paths to
a unique persistent directory under `Presets/assets/`. These checks detect
corruption; they are not a publisher signature.

Import saves the configuration without activating it, modifying AutoSave, or
contacting a device. Name collisions receive a numeric suffix. A failed import
removes its staged assets. Successfully imported assets are retained when a
preset is deleted because another preset or AutoSave may reference them.

## Diagnostic archive

Open **Settings → About → Export Diagnostics**, or **Export Diagnostics** in
the application log viewer. The editable preview contains application and
dependency versions, OS/Python details, selected boolean preferences, the
selected device's model/iOS/build when available, and up to the last 1 MiB of
the session log. It does not collect device backups or pairing files.

Known credentials, home paths, device identifiers and email addresses are
redacted. Review and edit the preview before sharing. Saving creates a local
ZIP with `diagnostics.json` and the previewed `session.log`; nothing is uploaded.

```sh
python nugget_cli.py diagnostics show --json
python nugget_cli.py diagnostics export --out diagnostics.zip --json
```

The CLI collects local settings and logs without discovering or querying devices.
Use `diagnostics show` to review the redacted report before exporting.

## CLI JSON and dry-run

Add `--json` before or after a command. Stdout contains one JSON document;
human messages and progress go to stderr. The version 1 envelope is:

```json
{"schema": 1, "command": "preset", "success": true, "exit_code": 0,
 "data": {"presets": []}, "error": null}
```

The managed commands return structured data for devices, tweaks, daemons,
presets, HotLoad, backups, diagnostics and wallpaper validation. Standalone
legacy commands return the same envelope with a bounded `data.output` text
field. Errors also use the envelope. Exit status is zero on success, nonzero
on failure; apply/reset return failure when completion is not confirmed.

```sh
python nugget_cli.py tweaks list --all --json
python nugget_cli.py preset list --json
python nugget_cli.py apply --dry-run --udid DEVICE_ID --json
python nugget_cli.py apply --dry-run --ios-version 27.0 --model iPhone16,1 \
  --preset none --enable SBBuildNumber --json
python nugget_cli.py reset --dry-run --springboard --json
```

`apply --dry-run` uses the saved preset plus the same command overrides as a
real apply. With `--ios-version` and `--model` it works entirely offline.
Without an offline version it discovers a connected device for its identity.
The plan includes selection differences, known plist writer paths,
compatibility issues, conflicts, skipped tweaks and forced daemon rules.
`ready` describes these static checks, not a guarantee that a restore will
succeed. An empty selection, missing referenced asset, incompatible tweak,
unknown model, kill switch or conflict makes the plan fail.

Dry-run generates no restore payloads and performs no backup, restore or
AutoSave. It does not probe live encryption, free space or the actual values
on the device. The plist list is not a complete restore manifest. Reset dry-run
lists the selected reset sections entirely offline; it does not validate a
target device.

## Wallpaper package reports

On the PosterBoard page, choose **Check Package…** for an unimported file or
**Check** next to an imported wallpaper. Inspection runs in the background;
the report can be saved as JSON. Templates (`.batter`) can also be checked.

```sh
python nugget_cli.py wallpaper validate wallpaper.tendies --json
python nugget_cli.py wallpaper validate template.batter --ios-version 27.0 --json
```

Checks cover ZIP integrity and paths, duplicate names, links, encryption,
unpacked size limits, descriptor count, plist/JSON/XML/CAML syntax and template
version constraints. Reports warn about embedded PosterBoard databases,
external script references and legacy wallpaper families. Model compatibility
and visual behavior cannot be verified by static inspection; unspecified
compatibility stays unknown. A report may pass with warnings.

Shared archive limits are 20,000 entries, 512 MiB per file and 2 GiB total
unpacked data, with a limit on excessive compression expansion. Structured
documents larger than 4 MiB receive a warning and are CRC-checked without
syntax parsing. At most 200 issues are displayed. Basic archive path checks
also run during normal wallpaper/template import.

## Offline regressions

```sh
QT_QPA_PLATFORM=offscreen python tools/test_portable_and_inspection.py
```

These tests exercise archive round trips and failure cleanup, diagnostics
redaction, CRC/syntax failures, background dialogs, typed JSON and dry-run
boundaries without a device or network.
