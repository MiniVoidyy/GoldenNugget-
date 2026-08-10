from PySide6.QtCore import QSettings

# Settings are stored under the "GoldenNugget" organization. Keys that are not
# present there fall back to the legacy "Nugget" organization so existing users
# keep their settings after the rename. Everything written goes to
# "GoldenNugget", which always takes priority when read back.

NEW_ORG = "GoldenNugget"
LEGACY_ORG = "Nugget"


class Settings:
    """Stores under "GoldenNugget" and reads through to "Nugget"."""

    def __init__(self, app: str = "settings"):
        self._primary = QSettings(NEW_ORG, app)
        self._legacy = QSettings(LEGACY_ORG, app)

    def contains(self, key: str) -> bool:
        return self._primary.contains(key) or self._legacy.contains(key)

    def value(self, key: str, defaultValue=None, type=None):
        # PySide6 6.11's QSettings.value crashes (SIGBUS in shiboken's
        # checkType) when None is passed positionally for the `type`
        # argument, so only forward it when an actual type is given.
        store = self._primary if self._primary.contains(key) else self._legacy
        if type is None:
            return store.value(key, defaultValue)
        return store.value(key, defaultValue, type)

    def setValue(self, key: str, value):
        self._primary.setValue(key, value)

    def remove(self, key: str):
        self._primary.remove(key)
        self._legacy.remove(key)

    def allKeys(self) -> list:
        keys = set(self._primary.allKeys())
        keys.update(self._legacy.allKeys())
        return list(keys)

    def sync(self):
        self._primary.sync()
        self._legacy.sync()
