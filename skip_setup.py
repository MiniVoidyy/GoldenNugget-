#! python3

import subprocess
import sys

def main(argv: list[str]):
    subprocess.run(
        [
            "cfgutil",
            "--ecid",
            argv[1],
            "prepare",
            "--skip-all"
        ]
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: skip_setup.py <ECID>")
        exit(1)
    main(sys.argv)