"""Repair source-built PySide wheel metadata without modifying binary payloads."""
from email import policy
from email.parser import BytesParser
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from packaging.tags import Tag, sys_tags
from packaging.utils import parse_wheel_filename


def normalize(path: Path) -> Path:
    name, version, _, tags = parse_wheel_filename(path.name)
    if name not in {'pyside6', 'shiboken6'} or any(
        tag.platform not in {'macosx_14_4_universal2', 'macosx_14_0_universal2'}
        for tag in tags
    ):
        raise ValueError(f'Unexpected source-built wheel: {path.name}')
    # packaging only emits major_0 macOS tags for macOS 11+.
    # The actual Mach-O deployment target remains 14.4.
    normalized_tags = {Tag(tag.interpreter, tag.abi, 'macosx_14_0_universal2')
                       for tag in tags}
    if not normalized_tags.intersection(sys_tags()):
        raise RuntimeError(f'Wheel ABI is incompatible with this Python: {path.name}')
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        # Unpack verifies the source RECORD. Pack derives the filename from
        # WHEEL metadata and regenerates RECORD, fixing PySide's extra Qt
        # build number in the original filename as well as its platform tag.
        subprocess.run([sys.executable, '-m', 'wheel', 'unpack', str(path),
                        '--dest', str(work)], check=True)
        unpacked, = work.iterdir()
        metadata_path, = unpacked.glob('*.dist-info/WHEEL')
        metadata = BytesParser(policy=policy.compat32).parsebytes(metadata_path.read_bytes())
        if set(metadata.get_all('Tag', [])) != {str(tag) for tag in tags}:
            raise ValueError(f'Filename and WHEEL tags disagree: {path.name}')
        del metadata['Tag']
        for tag in sorted(normalized_tags, key=str):
            metadata['Tag'] = str(tag)
        metadata_path.write_bytes(metadata.as_bytes())
        subprocess.run([sys.executable, '-m', 'wheel', 'pack', str(unpacked),
                        '--dest-dir', str(work)], check=True)
        packed, = work.glob('*.whl')
        packed_name, packed_version, _, packed_tags = parse_wheel_filename(packed.name)
        if (packed_name, packed_version, packed_tags) != (name, version, normalized_tags):
            raise ValueError(f'Unexpected repacked wheel: {packed.name}')
        result = path.with_name(packed.name)
        shutil.copy2(packed, result)
        if result != path:
            path.unlink()
        print(f'Normalized: {path.name} -> {result.name}', flush=True)
        return result


if __name__ == '__main__':
    for argument in sys.argv[1:]:
        normalize(Path(argument).resolve())
