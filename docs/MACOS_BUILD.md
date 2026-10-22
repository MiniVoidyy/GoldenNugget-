# Default macOS build

`.github/workflows/build.yml` defaults to Python **3.15.0**, Qt/PySide
**6.12.0**, Universal2 (`x86_64` and `arm64`), and **macOS 14.4 Sonoma**.
Qt 6.12's [supported-platform matrix](https://doc.qt.io/qt-6.12/supported-platforms.html#macos)
lists 14.4 as its macOS minimum.

The current PySide6 6.12 wheel contains Python bindings built with a macOS 26
minimum, even though its Qt frameworks target 14.4. The workflow therefore
builds Qt Core/Gui/Widgets/Network/Svg and the matching Python bindings from
the upstream `v6.12.0` sources on both native runners. Only runtime wheels are
cached and uploaded; the Shiboken generator and host LLVM remain build tools.

The packaging job uses the python.org Universal2 framework, merges native
wheels, then runs PyInstaller with `--target-arch=universal2`. macOS-specific
constraints retain a universal cryptography wheel with bundled OpenSSL and a
portable Crypto wheel. Other platforms keep their existing build jobs.

`tools/validate_macos.py` checks every Mach-O deployment target, required
architectures and non-system dependency paths. The bundle root uses Python's
universal SSL/zstd libraries; architecture-specific OpenCV codec libraries
keep their original paths. Any dependency above macOS 14.4 aborts packaging;
changing only Info.plist or a Mach-O load command is never a compatibility fix.

Artifacts: `Nugget-macOS-Universal2.dmg`, `Nugget-macOS-Universal.zip`, validation
JSON, dependency versions and SHA-256 checksums. Both archives contain a real
`Nugget.app`; the DMG also contains an Applications shortcut. Bundles are
ad-hoc signed and are not notarized. Frozen GUI/crypto smoke tests run on Intel
and Apple Silicon (macOS 15 runners); they do not constitute a runtime test
on macOS 14.4 itself.

First builds compile Qt and are slower. Subsequent builds reuse cached runtime
wheels keyed by architecture, Python/Qt version, target OS and build script.
