import sys
import os

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

# Import order matters: the gui package must load before device_manager to
# avoid a circular import (bookrestore -> apply_worker -> gui.pages -> tweaks
# -> pb_config_manager -> preference_manager).
from src.gui.pages import *
from src.controllers.settings import Settings
from src.devicemanagement.device_manager import DeviceManager
from src.tweaks.tweaks import tweaks, TweakID

QCoreApplication.setOrganizationDomain("com.leemin")
QCoreApplication.setApplicationName("GoldenNugget")

TENDIE = "/home/awesomenull/Загрузки/catvolleyball-lite.tendies"

app = QApplication(sys.argv)
settings = Settings("settings")
dm = DeviceManager()

def update_label(text):
    print("[STATUS]", text)

def show_alert(msg):
    if msg is None:
        print("[DONE] No alert")
        return
    print("[ALERT] ", getattr(msg, 'title', '') or 'Message')
    print("[ALERT]  ", getattr(msg, 'txt', msg))
    if getattr(msg, 'detailed_txt', None):
        print("[ALERT DETAIL]\n", msg.detailed_txt)

dm.get_devices(settings, show_alert=show_alert)
if dm.get_current_device_udid() is None:
    print("ERROR: No device connected!")
    sys.exit(1)

print("Device:", dm.get_current_device_name(), dm.get_current_device_version(), dm.get_current_device_build())
if not dm.get_current_device_is_supported_by_fork():
    print("ERROR: iOS version not supported by this fork!")
    sys.exit(1)

if not os.path.exists(TENDIE):
    print("ERROR: tendie not found:", TENDIE)
    sys.exit(1)

pb = tweaks[TweakID.PosterBoard]
pb.use_configs = True
added = pb.add_tendie(TENDIE)
print("Tendie added:", added, "| descriptors:", pb.get_descriptor_count())
if not added:
    print("ERROR: failed to add tendie")
    sys.exit(1)

print("Starting apply...")
dm.apply_changes(update_label=update_label, show_alert=show_alert)
print("Apply finished.")
