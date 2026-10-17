"""UI bookmarks, stored independently of tweak selections and presets."""
from PySide6.QtCore import QObject, Signal
from src.controllers.settings import Settings


class TweakFavorites(QObject):
    changed = Signal()
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def names(self):
        raw = Settings().value('favorite_tweaks', '', type=str) or ''
        return set(filter(None, raw.split(',')))

    def set_favorite(self, name, selected):
        names = self.names()
        if selected:
            names.add(name)
        else:
            names.discard(name)
        store = Settings()
        store.setValue('favorite_tweaks', ','.join(sorted(names)))
        store.sync()
        self.changed.emit()
