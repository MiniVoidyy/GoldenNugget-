import os
import zipfile
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ROOT), "GoldenNugget-v3.0.zip")

EXCLUDE_DIRS = {'.git', '__pycache__', 'build', 'dist', 'i18n'}
EXCLUDE_FILES = {'.DS_Store'}

def should_include(path: str) -> bool:
    rel = os.path.relpath(path, ROOT)
    if rel.startswith('.'):
        return rel in ('.gitattributes', '.gitignore', '.gitmodules')
    parts = rel.split(os.sep)
    if parts[0] in EXCLUDE_DIRS:
        return False
    if os.path.basename(path) in EXCLUDE_FILES:
        return False
    # skip compiled/cache
    if path.endswith(('.pyc', '.pyo')):
        return False
    return True

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if should_include(path):
                rel = os.path.relpath(path, ROOT).replace('\\', '/')
                z.write(path, rel)

print(f"Wrote {OUT} (size {os.path.getsize(OUT):,} bytes)")
