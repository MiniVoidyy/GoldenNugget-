import urllib.request
import json
from PySide6.QtWidgets import QMessageBox

CURRENT_VERSION = "v2"

def check_for_updates(parent=None):
    try:
        url = "https://api.github.com/repos/MiniVoidyy/GoldenNugget-/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "GoldenNugget"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            latest_tag = data.get("tag_name", "")
            html_url = data.get("html_url", "https://github.com/MiniVoidyy/GoldenNugget-/releases")
            if latest_tag and latest_tag != CURRENT_VERSION:
                QMessageBox.information(
                    parent,
                    "Update Available",
                    f"A new version ({latest_tag}) of GoldenNugget is available!\n\nCheck the GitHub releases page:\n{html_url}"
                )
    except Exception:
        pass
