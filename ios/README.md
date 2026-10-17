# GoldenNugget iOS (IPA)

On-device version of the GoldenNugget "Daemons to Disable" page. It
leverages [bad_query](https://github.com/forcequitOS/bad_query) (a sandbox
escape for iOS 26.0-26.6.1 / 27.0b4+) to write `/var/db/com.apple.xpc.launchd/disabled.plist`
directly on the device, so the daemon tweaks can be applied without a Mac
backup/restore round trip.

## Structure

```
ios/
  export_daemons_json.py          regenerates GoldenNugget/daemons.json from src/tweaks/daemons_tweak.py
  GoldenNugget.xcodeproj/         Xcode project (open this)
  GoldenNugget/
    GoldenNuggetApp.swift         app entry point
    ContentView.swift             daemon list UI + bad_query apply logic
    Daemon.swift                  JSON decoding + enabled-state store
    bad_query.c                   vendored sandbox escape (from forcequitOS/bad_query)
    bad_query.h
    GoldenNugget-Bridging-Header.h
    GoldenNugget.entitlements     app group used by bad_query
    Info.plist
    daemons.json                  generated from daemons_tweak.py
    Assets.xcassets/
```

## Keeping daemon data in sync

Run from the repo root after any edit to `src/tweaks/daemons_tweak.py`:

```
python -m pip install -e .   # ensure src is importable (first time only)
python ios/export_daemons_json.py
```

## Building the IPA

Requires macOS + Xcode 16+ (Xcode 26/27 works) and a device on
iOS 26+ / 27.0b4.

1. `open ios/GoldenNugget.xcodeproj`
2. In **Signing & Capabilities**:
   - set your **Team**
   - confirm the App Group `group.cc.forcequit.bad-query` is created/enabled
   - set bundle id (default `cc.forcequit.GoldenNugget`)
3. Build & run on device (generic iOS device if you only want the `.app`).
4. To produce the `.ipa`:
   - Product > Archive, then **Distribute App** or
   - `xcodebuild archive` + grab the `.app` from
     `DerivedData/.../Build/Products/Release-iphoneos` and zip it as
     `Payload/GoldenNugget.app`.
5. Sideload (TrollStore / Sideloadly / Xcode with free account for 7 days).

## Important

- This app writes a system plist via a privilege-escalation exploit.
  It can break the device if you disable core daemons (`keybagd`,
  `securityd`, `logd`, `syslogd`, `system.logger`, `hangreporter`,
  `spindump`, `apfsd`, MobileBackup). The desktop app deliberately keeps
  those OUT of the Recommended set for this reason.
- Only disable daemons you understand. Create a backup before use.
- The exploit works on iOS 26.0-26.6.1 and 27.0b4 only (per the bad_query README).