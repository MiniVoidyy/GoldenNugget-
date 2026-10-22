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

## Share codes and QR

**Share as QR** turns the selected preset into one line of text (`GN1.` +
base64url of zlib-compressed JSON) and the same code as a QR image, which can be
copied or saved as PNG. **Import Code** accepts the code pasted from anywhere
(surrounding text and line breaks are ignored), a QR screenshot or photo, or a
QR image on the clipboard; it shows the setup's risk verdict before saving it as
a new preset. Nothing is applied until the preset is loaded.

A code carries only the tweaks that are turned on. Templates, icon themes and
wallpapers are left out because they are files on the sender's computer. When
decoded, every other tweak is set to off, so loading the preset reproduces the
sender's setup instead of merging it into the current one. Codes are capped at
6000 characters and 256 KB after decompression, unknown tweak names are dropped,
and the result passes the same validation as an imported preset file. QR
encoding and decoding use OpenCV, which is already a dependency.

## Preset catalog

The **Community Catalog** page (its tile on the home screen, or **Browse
Catalog** on the Presets page) lists presets shared by the community.
Each one shows its author, iOS range, tags and a risk verdict for the connected
iPhone, and can be previewed on the virtual iPhone before **Import** saves it
as a new preset. As with share codes, nothing is applied until the preset is
loaded. With a device connected the list shows only presets made for its iOS
version; untick the box to see all.

The catalog is the `GoldenNugget-Team/GoldenNugget-Presets` repository: one
`presets/<id>.json` file per preset, holding a share code plus a name, author,
description, optional `ios_min`/`ios_max` and up to 8 tags. Every pull request
there is checked by `tools/preset_catalog.py check` (run from this repository's
`main`, through `pull_request_target`, so a pull request cannot change its own
check). The check validates each file, rejects duplicate codes, stops anyone
outside the team from touching files other than `presets/*.json` and writes a
risk table to the pull request. Maintainers review and merge; after a merge
`tools/preset_catalog.py build` writes `index.json`, which GitHub Pages serves
to the app (`src/controllers/preset_catalog.py`, `INDEX_URL`).

The app treats the index as untrusted: it is size-capped, every row is
validated again with the same rules and its share code is decoded locally;
damaged rows are skipped. The last good index is cached, so the catalog still
opens offline.

**Submit to Catalog** fills in the catalog details for the selected preset and
opens GitHub's "new file" page with the file already written; GitHub forks the
repository and opens the pull request for people without write access. When
the file is too long for a URL, it goes to the clipboard instead.

The **Templates** tab lists `.batter` templates from `templates/<id>.batter`
in the same repository. The check loads each one with the app's template rules
and the static validator, and the pull request summary lists every file each
template's tweaks write (see "Community Tweaks" in `documentation.md`).
`build` copies the templates next to `index.json` and records their size and
SHA-256. **Download and Add** fetches a template only from `TEMPLATES_URL` by
id, refuses it when the size or hash differs, stores it in the app data folder
(`catalog_templates/`) and adds it to PosterBoard → Templates, replacing an
older copy. Older app versions ignore the `templates` key of the index.

Imported presets remember their catalog id and a hash of their share code
(`metadata.catalog`); downloaded templates are compared by SHA-256. When the
catalog has a different version, the entry says **Update available**, its
button becomes **Update** (a preset update replaces the imported preset under
its current name) and the Community Catalog row on the home screen counts the
updates, using the cached index only.

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
