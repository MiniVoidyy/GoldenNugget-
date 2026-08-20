# Changelog

All notable changes to GoldenNugget are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to the versioning described below.

---

## [8.3] — 2026-08-20 — FINAL (stable)

> This is the **last 8.x release** on the `main` branch. After this release,
> active development moves to a separate unstable branch **`dev-9.0`** for a
> major rework of the codebase.

8.3 was first released, then **recalled due to a regression**, and finally
rebuilt through `8.3 beta 1` → `8.3 beta 2` → this cleaned, verified final.

### The path to 8.3 (honest history)

- **8.3 (original, recalled)** — Released early with a new protective-backup
  scope that included `ConfigurationProfiles` (MDM/VPN/WebClip profiles,
  commit `25006f5`). On-device testing showed this widened the Phase 3
  restore scope enough to **roll back applied tweaks on a repeat apply** and
  **corrupt the PosterBoard database**. The release was withdrawn.
- **Hotfix (`875d4e1`)** — The Phase 3 scope was reverted to the narrow
  pre-fix state: `ManagedPreferencesDomain`/`SystemPreferencesDomain`
  `ConfigurationProfiles` handling and the "Phase 4" encrypted keychain
  backup were removed. The regression that caused the recall is documented
  inline in `src/restore/protective.py` so it is not re-introduced.
- **8.3 beta 1** — Version bumped after the hotfix; continued QOL work.
- **8.3 beta 2** — Encrypted backup support, i18n integration, iOS-style UI
  improvements, auto-save presets, and PosterBoard fixes.
- **8.3 final** — Legacy code cleanup + iOS UI parity pass + full regression
  verification (see below). **Final on-device verification checklist is
  still pending a human run before this release is published.**

### New in 8.3 final

- **iOS-style UI (new UI) is now feature-complete** — every feature available
  in the classic UI is reachable in the new UI:
  - Added a **Feature Flags** section (Clock Anim, Lock Screen, Kiosk Mode,
    Solarium feature-flag groups) — previously only in the classic UI.
  - Added the **Passcode Themes** page (import `.passthm`, key size, language
    code, discover) — previously missing.
  - **Springboard** page is now reachable from the iOS home; `Auto-Lock`
    (lock screen idle time) is a proper numeric input instead of a broken
    switch.
  - Status Bar page gained the missing Cellular Service show/hide controls;
    PosterBoard video tab now matches classic (calculation mode, export video
    loop, discover wallpapers, help).
  - The classic ↔ iOS UI toggle switches cleanly without losing the selected
    tweaks state (both UIs share the same `tweaks` state).
- **Legacy code cleanup** — removed dead artifacts of removed subsystems
  (bookrestore data files, eligibility-era files, `.on_device_remote_files`,
  broken status-bar test scripts referencing the removed `use_bookrestore`
  parameter, unused imports and dead functions). No import points to a
  missing module; `py_compile` is clean.
- **Regression verification** — full headless regression suite (189 checks)
  over the apply/backup/restore flow, the Phase 3 scope revert, the iOS UI
  toggle, PosterBoard reset scheduling, and i18n. No new regressions found.
  A PyInstaller build (`compile.py`) succeeds.

### On-device verification still required (cannot be automated)

Before publishing, confirm on a real device:

1. Apply tweak set A → apply set B → B sticks and A does not roll back
   (repeat apply on iOS 27 — the 8.3 regression scenario).
2. Full Phase 1→2→3 cycle three times in a row → PosterBoard database stays
   valid (not malformed).
3. Reset PosterBoard from the new UI actually clears collections/gallery.
4. Encrypted backup cycle ×2 in a row completes without failures.
5. Language switching (incl. Arabic RTL) does not crash the app.

---

## [8.2.1] — 2026-08-12

- iOS 27 status bar research: Speakeasy gate blocked; classic
  `statusBarOverrides` path preserved as fallback.

## [8.2] — 2026-08

- iOS 27 support refinements, PosterBoard fixes.

## [8.1] — 2026-07

- Stability and bug fixes.

## [8.0] — 2026-07

- Initial 8.x release.