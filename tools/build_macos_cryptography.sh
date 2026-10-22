#!/usr/bin/env bash
# Build both slices without running target executables or linking Homebrew dylibs.
set -euo pipefail
build_root="${RUNNER_TEMP:?}/goldennugget-cryptography"
wheels="$PWD/.macos-cryptography-wheels"
mkdir -p "$build_root" "$wheels"
export MACOSX_DEPLOYMENT_TARGET=14.4
export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
export RUSTUP_TOOLCHAIN=stable
jobs="${GOLDENNUGGET_BUILD_JOBS:-$(sysctl -n hw.ncpu)}"
if ! [[ "$jobs" =~ ^[1-9][0-9]*$ ]]; then
  echo "::error::GOLDENNUGGET_BUILD_JOBS must be a positive integer"
  exit 1
fi
rustup target add aarch64-apple-darwin x86_64-apple-darwin
python -m pip install 'maturin>=1.14.1,<2' 'cffi>=2.1' setuptools wheel

python - "$build_root" <<'FETCH'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

root = Path(sys.argv[1])
release_path = root / 'cryptography-release.json'
subprocess.run(['curl', '--fail', '--location', '--retry', '3', '--output', str(release_path),
                'https://pypi.org/pypi/cryptography/50.0.0/json'], check=True)
release = json.loads(release_path.read_text())
sdist, = [item for item in release['urls'] if item['packagetype'] == 'sdist']
sources = [
    ('cryptography', sdist['url'], sdist['digests']['sha256']),
    ('openssl', 'https://github.com/openssl/openssl/releases/download/openssl-3.5.9/openssl-3.5.9.tar.gz',
     '603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a'),
]
for name, url, checksum in sources:
    archive = root / f'{name}.tar.gz'
    subprocess.run(['curl', '--fail', '--location', '--retry', '3', '--output', str(archive), url], check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
        raise SystemExit(f'SHA256 mismatch: {name}')
    destination = root / name
    destination.mkdir()
    with tarfile.open(archive) as source:
        source.extractall(destination, filter='data')
    extracted, = destination.iterdir()
    extracted.rename(root / f'{name}-source')
FETCH

# OpenSSL configures each architecture independently. Only its libraries and
# headers are built/installed: an Intel executable is never run on the ARM host.
for arch in arm64 x86_64; do
  if [ "$arch" = arm64 ]; then
    target=darwin64-arm64-cc
  else
    target=darwin64-x86_64-cc
  fi
  mkdir -p "$build_root/openssl-build-$arch"
  (
    cd "$build_root/openssl-build-$arch"
    CC=/usr/bin/clang perl "$build_root/openssl-source/Configure" "$target" \
      no-shared no-tests no-module --libdir=lib \
      --prefix="$build_root/openssl-$arch" \
      -mmacosx-version-min=14.4 -isysroot "$SDKROOT"
    make -j "$jobs" build_libs
    make install_dev
  )
done
export OPENSSL_STATIC=1
export OPENSSL_NO_VENDOR=1
export AARCH64_APPLE_DARWIN_OPENSSL_DIR="$build_root/openssl-arm64"
export X86_64_APPLE_DARWIN_OPENSSL_DIR="$build_root/openssl-x86_64"
cd "$build_root/cryptography-source"
python -m maturin build --release --target universal2-apple-darwin \
  --interpreter "$(command -v python)" --jobs "$jobs" --out "$wheels"

python - "$wheels" <<'CHECK'
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

wheel, = Path(sys.argv[1]).glob('*.whl')
name, version, _, tags = parse_wheel_filename(wheel.name)
assert name == 'cryptography' and str(version) == '50.0.0', wheel
assert any(tag.platform.endswith('_universal2') for tag in tags), wheel
assert tags.intersection(sys_tags()), f'Unsupported wheel tags: {wheel.name}'
with zipfile.ZipFile(wheel) as archive, tempfile.TemporaryDirectory() as directory:
    extensions = [item for item in archive.namelist() if item.endswith('.so')]
    assert extensions, 'Missing cryptography extension'
    for item in extensions:
        binary = Path(directory) / Path(item).name
        binary.write_bytes(archive.read(item))
        arches = set(subprocess.check_output(['lipo', '-archs', str(binary)], text=True).split())
        assert {'arm64', 'x86_64'} <= arches, (item, arches)
        libraries = subprocess.check_output(['otool', '-L', str(binary)], text=True)
        assert not any(value in libraries for value in ('/opt/homebrew/', '/usr/local/', 'libssl.', 'libcrypto.')), libraries
print(f'Static Universal2 cryptography verified: {wheel.name}')
CHECK
