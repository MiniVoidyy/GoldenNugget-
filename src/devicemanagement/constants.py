from packaging.version import Version


class Device:
    def __init__(self, 
                udid: int, usb: bool, name: str,
                version: str, build: str,
                model: str, hardware: str, cpu: str, locale: str
            ):
        self.udid = udid
        self.connected_via_usb = usb
        self.name = name
        self.version = version
        self.build = build
        self.model = model
        self.hardware = hardware
        self.cpu = cpu
        self.locale = locale

def is_supported_by_fork(version: str) -> bool:
    # this fork only supports iOS 26.2 and newer (the iOS 27 era)
    return Version(version) > Version("26.1")