import plistlib

from PySide6.QtCore import QSettings, QStandardPaths
from os import path, makedirs
from os import remove as rmfile
from shutil import copyfile
from typing import Optional

from src.tweaks.posterboard.pb_config_item import PBConfigItem
from src.controllers.settings import Settings

class PreferenceManager:
    def __init__(self, settings: QSettings):
        self.settings = settings
        self.apply_over_wifi = False
        self.auto_reboot = True
        self.show_all_spoofable_models = False
        self.disable_tendies_limit = False
        self.auto_refresh_posterboard = True
        self.rebuild_sb_application_state_db = False
        self.restore_truststore = False
        self.use_encrypted_backup = False
        self.skip_setup = True
        self.supervised = False
        self.organization_name = ""

    # Original Plist Saving
    def get_original_plists_prefs(self) -> QSettings:
        return Settings("Original Plists")

    def _original_plist_key(self, model: str, build: str, path: str) -> str:
        return f"{model}|{build}|{path}"

    def save_original_plist(self, model: str, build: str, path: str, contents: bytes):
        self.get_original_plists_prefs().setValue(
            self._original_plist_key(model, build, path), contents)

    def get_original_plist(self, model: str, build: str, path: str) -> Optional[bytes]:
        settings = self.get_original_plists_prefs()
        key = self._original_plist_key(model, build, path)
        if not settings.contains(key):
            return None
        data = settings.value(key)
        if data is None:
            return None
        return bytes(data)

    def has_original_plist(self, model: str, build: str, path: str) -> bool:
        return self.get_original_plists_prefs().contains(
            self._original_plist_key(model, build, path))

    def has_nonempty_original_plist(self, model: str, build: str, path: str) -> bool:
        """True when a usable (non-empty) original is stored for this path.

        Empty dicts are the nulled state resets write, so they never count as
        an original.
        """
        data = self.get_original_plist(model, build, path)
        if data is None:
            return False
        try:
            return plistlib.loads(bytes(data)) != {}
        except Exception:
            return False

    def get_original_plists(self, model: str, build: str) -> dict[str, bytes]:
        settings = self.get_original_plists_prefs()
        prefix = f"{model}|{build}|"
        result: dict[str, bytes] = {}
        for key in settings.allKeys():
            if key.startswith(prefix):
                data = settings.value(key)
                if data is not None:
                    result[key[len(prefix):]] = bytes(data)
        return result

    def has_any_original_plists(self, model: str, build: str) -> bool:
        """True when at least one non-empty original plist is stored for this
        model/build.

        Empty dicts are the nulled state resets write — older versions could
        save them as "originals" (captured from a device that was already
        reset), poisoning the store forever. They do not count here so a
        poisoned capture is redone on the next apply.
        """
        settings = self.get_original_plists_prefs()
        prefix = f"{model}|{build}|"
        for key in settings.allKeys():
            if key.startswith(prefix):
                data = settings.value(key)
                if data is None:
                    continue
                try:
                    if plistlib.loads(bytes(data)) != {}:
                        return True
                except Exception:
                    continue
        return False

    def remove_original_plists(self, model: str, build: str):
        settings = self.get_original_plists_prefs()
        prefix = f"{model}|{build}|"
        for key in list(settings.allKeys()):
            if key.startswith(prefix):
                settings.remove(key)

    # Last Apply Snapshot (for reverting the most recent apply)
    def get_last_apply_prefs(self) -> QSettings:
        return Settings("Last Apply")

    def save_last_apply(self, udid: str, files: dict):
        self.get_last_apply_prefs().setValue(udid, files)

    def get_last_apply(self, udid: str) -> Optional[dict]:
        settings = self.get_last_apply_prefs()
        if not settings.contains(udid):
            return None
        data = settings.value(udid)
        if data is None:
            return None
        return {str(k): bytes(v) for k, v in data.items()}

    def has_last_apply(self, udid: str) -> bool:
        return self.get_last_apply_prefs().contains(udid)

    def remove_last_apply(self, udid: str):
        self.get_last_apply_prefs().remove(udid)

    # PosterBoard Configuration Database Saving
    def get_pbconfigs_prefs() -> QSettings:
        return Settings("PB Configs")
    def get_pbconfigs_db_save_path(udid: Optional[str]=None) -> str:
        app_data_path = path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), "PB_Saved_Databases")
        if not path.exists(app_data_path):
            makedirs(app_data_path)
        if udid is not None:
            app_data_path = path.join(app_data_path, f'{udid}.sqlite3')
        return app_data_path
    
    def save_pbconfig_file(filepath: str, udid: str):
        pbdb_path = PreferenceManager.get_pbconfigs_db_save_path(udid)
        copyfile(filepath, pbdb_path)
    def save_pbconfig_ids(ids: list[PBConfigItem], udid: str):
        pbc_settings = PreferenceManager.get_pbconfigs_prefs()
        # convert it to serializable data
        serialized_ids: list[dict] = []
        for id in ids:
            serialized_ids.append(id.to_dict())
        pbc_settings.setValue(udid, serialized_ids)

    def remove_pbconfig_data(udid: str):
        pbdb_path = PreferenceManager.get_pbconfigs_db_save_path(udid)
        if path.exists(pbdb_path):
            rmfile(pbdb_path)
            PreferenceManager.remove_pbconfig_ids(udid)
    def remove_pbconfig_ids(udid: str):
        pbc_settings = PreferenceManager.get_pbconfigs_prefs()
        if pbc_settings.contains(udid):
            pbc_settings.remove(udid)

    def has_pbconfig_data(udid: str) -> bool:
        return path.exists(PreferenceManager.get_pbconfigs_db_save_path(udid))
    def has_pbconfig_ids(udid: str) -> bool:
        return PreferenceManager.get_pbconfigs_prefs().contains(udid)
    
    def get_pbconfig_path(udid: str) -> Optional[str]:
        pbdb_path = PreferenceManager.get_pbconfigs_db_save_path(udid)
        if path.exists(pbdb_path):
            return pbdb_path
        return None
    def get_pbconfig_ids(udid: str) -> list[PBConfigItem]:
        pbc_settings = PreferenceManager.get_pbconfigs_prefs()
        if not pbc_settings.contains(udid):
            return []
        serialized_ids = pbc_settings.value(udid)
        if serialized_ids is None:
            return []
        ids: list[PBConfigItem] = []
        for id in serialized_ids:
            ids.append(PBConfigItem.from_dict(id))
        return ids