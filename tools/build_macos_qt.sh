#!/usr/bin/env bash
# Qt's official 6.12 frameworks target 14.4, but its Python binding wheel
# contains macOS 26 bindings. Rebuild both, never rewrite Mach-O minimums.
set -euo pipefail
qt_version=6.12.0
build_root="${RUNNER_TEMP:?}/goldennugget-qt"
qt_prefix="$build_root/Qt"
wheels="$PWD/.macos-qt-wheels"
mkdir -p "$build_root" "$wheels"
export MACOSX_DEPLOYMENT_TARGET=14.4
build_jobs="${GOLDENNUGGET_BUILD_JOBS:-$(sysctl -n hw.ncpu)}"
if ! [[ "$build_jobs" =~ ^[1-9][0-9]*$ ]]; then
  echo "::error::GOLDENNUGGET_BUILD_JOBS must be a positive integer"
  exit 1
fi
export CMAKE_BUILD_PARALLEL_LEVEL="$build_jobs"
echo "Building with $build_jobs compiler jobs"
brew install cmake ninja llvm
export LLVM_INSTALL_DIR="$(brew --prefix llvm)"
python -m pip install --upgrade pip setuptools wheel packaging build numpy
python - <<'ARCH'
import platform
assert platform.machine() == 'arm64', 'Run this build natively on Apple Silicon'
import sysconfig
assert sysconfig.get_platform().endswith('-universal2'), 'Use universal2 Python'
ARCH

for module in qtbase qtsvg; do
  git clone --depth 1 --branch "v${qt_version}" "https://github.com/qt/${module}.git" "$build_root/$module"
done
cmake -S "$build_root/qtbase" -B "$build_root/qtbase-build" -G Ninja \
  -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$qt_prefix" \
  -DCMAKE_OSX_DEPLOYMENT_TARGET="$MACOSX_DEPLOYMENT_TARGET" \
  -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF \
  -DFEATURE_openssl=OFF -DFEATURE_dbus=OFF -DFEATURE_icu=OFF \
  -DFEATURE_zstd=OFF -DFEATURE_system_zlib=OFF \
  -DFEATURE_system_pcre2=OFF -DFEATURE_system_libpng=OFF \
  -DFEATURE_system_libjpeg=OFF -DFEATURE_system_freetype=OFF \
  -DFEATURE_system_harfbuzz=OFF
cmake --build "$build_root/qtbase-build" --parallel "$build_jobs"
cmake --install "$build_root/qtbase-build"
git clone --depth 1 --branch "v${qt_version}" \
  https://github.com/pyside/pyside-setup.git "$build_root/pyside-setup"
cd "$build_root/pyside-setup"
# This runtime-only Qt build has no Assistant/Designer/Linguist apps.
# PySide otherwise tries to install those bundles from qttools and fails.
# Resources and translations are already compiled and committed in src/qt.
pyside_args=(
  --qtpaths="$qt_prefix/bin/qtpaths6"
  --standalone --ignore-git --skip-docs --no-qt-tools
  --module-subset=Core,Gui,Widgets,Network,Svg
  --macos-deployment-target="$MACOSX_DEPLOYMENT_TARGET"
)
build_qtsvg() (
  jobs="$1"
  cmake -S "$build_root/qtsvg" -B "$build_root/qtsvg-build" -G Ninja \
    -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$qt_prefix" \
    -DCMAKE_INSTALL_PREFIX="$qt_prefix" \
    -DCMAKE_OSX_DEPLOYMENT_TARGET="$MACOSX_DEPLOYMENT_TARGET" \
    -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF
  cmake --build "$build_root/qtsvg-build" --parallel "$jobs"
  cmake --install "$build_root/qtsvg-build"
)
build_shiboken_generator() (
  # No wheel packaging: this host tool only needs its CMake installation.
  # This also avoids scanning Qt's prefix while QtSvg is being installed.
  python setup.py build "${pyside_args[@]}" --parallel="$1" --skip-packaging \
    --build-type=shiboken6-generator --macos-arch=arm64 \
    --internal-cmake-install-dir-query-file-path="$build_root/shiboken-host.txt"
)
# QtSvg and the native generator depend only on QtBase, not on each other.
# Share one CPU budget rather than oversubscribing both Ninja processes.
if [ "$build_jobs" -gt 1 ]; then
  svg_jobs=$((build_jobs / 2))
  host_jobs=$((build_jobs - svg_jobs))
  build_qtsvg "$svg_jobs" &
  svg_pid=$!
  build_shiboken_generator "$host_jobs" &
  host_pid=$!
  result=0
  wait "$svg_pid" || result=$?
  wait "$host_pid" || result=$?
  if [ "$result" -ne 0 ]; then
    echo "::error::Parallel QtSvg / Shiboken generator build failed"
    exit "$result"
  fi
else
  build_qtsvg 1
  build_shiboken_generator 1
fi
shiboken_host="$(cat "$build_root/shiboken-host.txt")"
# Both Python slices share sysconfig and headers. Find the native generator
# through CMake's normal search path: --shiboken-host-path would incorrectly
# enable cross-build mode and require a target Python_SOABI.
export CMAKE_PREFIX_PATH="$shiboken_host${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
# Only runtime libraries get both slices; all build tools execute natively.
for module in shiboken6 pyside6; do
  python setup.py bdist_wheel "${pyside_args[@]}" \
    --build-type="$module" --macos-arch="arm64;x86_64" --parallel="$build_jobs"
done
# The generator is a build tool linked to host LLVM; never ship it.
for wheel in dist/*.whl; do
  case "$(basename "$wheel")" in
    shiboken6-[0-9]*.whl|[Pp]y[Ss]ide6-[0-9]*.whl) cp "$wheel" "$wheels/" ;;
  esac
done
python - "$wheels" <<'CHECK'
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from packaging.utils import parse_wheel_filename
wheel_paths = list(Path(sys.argv[1]).glob('*.whl'))
names = {parse_wheel_filename(p.name)[0] for p in wheel_paths}
assert names == {'pyside6', 'shiboken6'}, names
magics = {b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf',
          b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
          b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca'}
for wheel_path in wheel_paths:
    tags = parse_wheel_filename(wheel_path.name)[3]
    assert all(tag.platform.endswith('_universal2') for tag in tags), wheel_path
    binaries = 0
    with zipfile.ZipFile(wheel_path) as wheel, tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp) / 'binary'
        for entry in wheel.infolist():
            with wheel.open(entry) as stream:
                if stream.read(4) not in magics:
                    continue
            binary.write_bytes(wheel.read(entry))
            slices = set(subprocess.check_output(['lipo', '-archs', str(binary)], text=True).split())
            assert {'arm64', 'x86_64'} <= slices, (wheel_path, entry.filename, slices)
            binaries += 1
    assert binaries, f'No Mach-O binaries found in {wheel_path}'
    print(f'Universal2 wheel verified: {wheel_path.name} ({binaries} binaries)')
CHECK
