from pathlib import Path

from src.devicemanagement.constants import Device, Tweak

class DataSingleton:
    def __init__(self):
        self.current_device: Device = None
        self.device_available: bool = False