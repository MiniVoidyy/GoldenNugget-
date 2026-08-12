![Artboard][NuggetLogo]

# GoldenNugget
Unlock your device's full potential!

Customize your device with animated wallpapers, disable pesky daemons, and more!

Make sure you have installed the [requirements](#requirements) if you are on Windows or Linux.

> [!WARNING]
> You will need to re-login in your apple ID if using on IOS 27

> [!WARNING]
> This fork implements a three-phase backup→tweak→restore workflow to prevent data loss on iOS 27. Apple has patched the partial restore method that Nugget uses, so applying tweaks directly now triggers a security response that wipes AppleID, Keychain, Photos and settings. This fork preserves your data by backing it up first, then restoring it after the tweak is applied. Control Center module layout and home screen are also preserved. **THIS WORKAROUND IS UNSTABLE NOW, I AM NOT RESPONSIBLE FOR ANY DATA LOSS/BOOTLOOP CAUSED BY GOLDENNUGGET.**

> [!NOTE]
> Please back up your data before using this Project! GoldenNugget may cause unforeseen problems, so it is better to be safe than sorry. We are not responsible for any damage done to your device.

## Features
<details>
<summary>iOS 26.2 - 27.0+</summary>

- PosterBoard: Animated wallpapers and descriptors.
  - Community wallpapers can be found [here][WallpapersWebsite]
  - Customizing community-made wallpapers via batter files
  - See documentation on the structure of tendies and batter files in [documentation.md](documentation.md)
- Templates: Custom Operations and file editing
  - See documentation on the structure of batter files in [documentation.md](documentation.md)
- psysbackup: backup system plist
  - Required to make "reset tweaks" function work without damaging system.
- Revert Last Apply: restore your device to its exact state before the most
  recent apply with one click
- Status Bar (iOS 27: blocked by Speakeasy gate — see RESEARCH_SUMMARY.md)
  - Change carrier name
  - Change secondary carrier name
  - Enable/Disable the primary or secondary carriers
  - Change the number of WiFi/Cellular bars
  - Change the battery capacity
  - Change battery display detail
  - Change time text
  - Change date text (iPad only)
  - Change breadcrumb text
  - Show numeric WiFi/Cellular strength
  - Hide or show many icons in the status bar
- Springboard Options
  - Set Lock Screen Footnote
