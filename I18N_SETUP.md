# gNugget-i18n Integration Setup

This document explains how to set up crowdsourced translations via the [gNugget-i18n](https://github.com/awesomenull-dev/gNugget-i18n) repository.

## Architecture

```
gNugget-i18n repo (crowdsourced translations)
       │
       ▼ (push to main / PR merged)
GitHub Actions: notify-goldennugget-i18n.yml
       │
       ▼ (repository_dispatch)
GoldenNugget repo: sync-translations.yml
       │
       ├── Pull translations from gNugget-i18n
       ├── Merge into .ts files
       ├── Compile .qm files (pyside6-lrelease)
       ├── Regenerate resources_rc.py (pyside6-rcc)
       └── Create PR with changes
```

## Required Secrets

In **GoldenNugget** repo:
- `GH_PAT` - Personal Access Token with `repo` scope (for creating PRs)

In **gNugget-i18n** repo:
- `GH_PAT` - Personal Access Token with `repo` scope (to dispatch to GoldenNugget)

## Manual Sync

To manually sync translations:

```bash
# From GoldenNugget root
python scripts/sync_translations.py /path/to/gNugget-i18n src/qt/translations
cd src/qt/translations
for f in *.ts; do pyside6-lrelease "$f" -qm "${f%.ts}.qm"; done
cd ..
pyside6-rcc resources.qrc -o resources_rc.py
```

## Automatic Sync

1. **Weekly**: Runs every Sunday 3 AM UTC
2. **On translation updates**: When gNugget-i18n receives new translations

## Adding New Languages

1. Add new `.ts` file to gNugget-i18n repo (e.g., `Nugget_xx.ts`)
2. Translators contribute via PRs
3. On merge, GoldenNugget will automatically:
   - Detect new language file
   - Copy to src/qt/translations/
   - Compile .qm
   - Update resources_rc.py
   - Create PR

## Local Development

For testing translations locally:

```bash
# Set up test environment
export GOLDENNUGGET_LOG_FILE=/tmp/goldennugget.log
python main_app.py --test-mode --debug
```

## Translation File Format

Files use Qt Linguist `.ts` format (XML). Each file contains:
- Contexts (UI pages/widgets)
- Messages with source text and translations
- Metadata (translator comments, etc.)

Example:
```xml
<context>
    <name>MainWindow</name>
    <message>
        <source>Settings</source>
        <translation>Настройки</translation>
    </message>
</context>
```

## CI/CD Pipeline

The sync runs in this order:
1. `notify-goldennugget-i18n.yml` (gNugget-i18n repo) → dispatches event
2. `sync-translations.yml` (GoldenNugget repo):
   - Clones both repos
   - Merges translations using `scripts/sync_translations.py`
   - Compiles `.ts` → `.qm` with `pyside6-lrelease`
   - Regenerates `resources_rc.py` with `pyside6-rcc`
   - Creates PR with changes
3. Maintainer reviews and merges PR

## Testing Translations

To test a specific language:

```bash
# Force specific locale
export LANG=ru_RU.UTF-8
python main_app.py --test-mode
```

Or in code:
```python
translator.set_new_language("ru", restart=False)
```