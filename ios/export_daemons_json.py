"""Export ALL daemon definitions from daemons_tweak.py into daemons.json.

Run from the repo root so `src.tweaks` resolves:
    python ios/export_daemons_json.py

Writes ios/GoldenNugget/daemons.json consumed by the SwiftUI IPA so the
on-device daemon disabler stays in sync with the desktop app's list.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tweaks.daemons_tweak import (
    Daemon,
    DAEMON_CATEGORY,
    DAEMON_TITLES,
    DAEMON_DESCRIPTIONS,
    RECOMMENDED_ANALYTICS,
    DaemonCategory,
)


def main():
    out = []
    for daemon in Daemon:
        category = DAEMON_CATEGORY.get(daemon, DaemonCategory.OTHER)
        out.append({
            "name": daemon.name,
            "labels": list(daemon.value),
            "category": category.name,
            "title": DAEMON_TITLES.get(daemon, daemon.name),
            "description": DAEMON_DESCRIPTIONS.get(daemon.name, ""),
        })

    payload = {
        "generated_from": "src/tweaks/daemons_tweak.py",
        "recommended": [
            d.name for d in RECOMMENDED_ANALYTICS
        ],
        "daemons": out,
    }

    dest = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "GoldenNugget",
        "daemons.json",
    )
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} daemons to {dest}")


if __name__ == "__main__":
    main()