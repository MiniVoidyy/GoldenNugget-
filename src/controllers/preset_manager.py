import base64
import json
import os
import time
from typing import Optional

from PySide6.QtCore import QStandardPaths

from src.tweaks.tweak_names import TweakID
from src.tweaks import tweak_loader
from src.tweaks.tweaks import tweaks
from src.tweaks.tweak_classes import (
    BasicPlistTweak, AdvancedPlistTweak,
)
from src.tweaks.posterboard.posterboard_tweak import PosterboardTweak
from src.tweaks.posterboard.template_options.templates_tweak import TemplatesTweak
from src.tweaks.status_bar.status_bar_tweak import StatusBarTweak
from src.tweaks.passcode_theme_tweak import PasscodeThemeTweak
from src.tweaks.status_bar.status_bar_c.status_setter import ffi as status_ffi

PRESETS_DIR_NAME = "Presets"
PRESET_VERSION = 2

class PresetManager:
    def __init__(self):
        base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        # Ensure GoldenNugget-specific folder
        if not base_dir.endswith("GoldenNugget") and not base_dir.endswith("GoldenNugget/"):
            base_dir = os.path.join(base_dir, "GoldenNugget")
        self.presets_dir = os.path.join(base_dir, PRESETS_DIR_NAME)
        os.makedirs(self.presets_dir, exist_ok=True)

    def get_preset_path(self, name: str) -> str:
        safe_name = self._sanitize_name(name)
        return os.path.join(self.presets_dir, f"{safe_name}.json")

    def _sanitize_name(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        return safe or "Preset"

    def list_presets(self) -> list[str]:
        presets = []
        if not os.path.isdir(self.presets_dir):
            return presets
        for file in sorted(os.listdir(self.presets_dir)):
            if file.lower().endswith(".json"):
                presets.append(os.path.splitext(file)[0])
        return presets

    def get_preset_metadata(self, name: str) -> Optional[dict]:
        """Get metadata for a preset without loading the full data."""
        file_path = self.get_preset_path(name)
        if not os.path.isfile(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("metadata", {})
        except Exception:
            return None

    def list_presets_with_metadata(self) -> list[dict]:
        """List all presets with their metadata."""
        result = []
        for name in self.list_presets():
            meta = self.get_preset_metadata(name)
            if meta:
                result.append({
                    "name": name,
                    "description": meta.get("description", ""),
                    "device_model": meta.get("device_model", "Unknown"),
                    "ios_version": meta.get("ios_version", "Unknown"),
                    "created_at": meta.get("created_at", 0),
                    "updated_at": meta.get("updated_at", 0),
                    "tags": meta.get("tags", []),
                    "version": meta.get("version", 1),
                })
        return sorted(result, key=lambda x: x.get("updated_at", 0), reverse=True)

    def save_preset(self, name: str, description: str = "", tags: list = None,
                    device_model: str = "", ios_version: str = "") -> bool:
        data = self._serialize()
        if data is None:
            return False
        
        # Add metadata
        now = int(time.time())
        meta = {
            "version": PRESET_VERSION,
            "description": description or "",
            "device_model": device_model or "Unknown",
            "ios_version": ios_version or "Unknown",
            "created_at": now,
            "updated_at": now,
            "tags": tags or [],
        }
        # Preserve original creation time if updating
        existing_meta = self.get_preset_metadata(name)
        if existing_meta and "created_at" in existing_meta:
            meta["created_at"] = existing_meta["created_at"]
        
        data["metadata"] = meta
        
        file_path = self.get_preset_path(name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save preset: {e}")
            return False

    def load_preset(self, name: str) -> bool:
        file_path = self.get_preset_path(name)
        if not os.path.isfile(file_path):
            return False
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to read preset: {e}")
            return False
        return self._apply(data)

    def delete_preset(self, name: str) -> bool:
        file_path = self.get_preset_path(name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Failed to delete preset: {e}")
        return False

    ## EXPORT / IMPORT
    def export_preset(self, name: str, export_path: str) -> bool:
        """Export a preset to a shareable JSON file."""
        file_path = self.get_preset_path(name)
        if not os.path.isfile(file_path):
            return False
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Add export marker
            data["exported"] = True
            data["exported_at"] = int(time.time())
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to export preset: {e}")
            return False

    def import_preset(self, import_path: str, new_name: str = None) -> tuple[bool, str]:
        """Import a preset from a JSON file. Returns (success, actual_name)."""
        if not os.path.isfile(import_path):
            return False, "File not found"
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate structure
            if "tweaks" not in data and "metadata" not in data:
                return False, "Invalid preset format"
            
            # Determine name
            if new_name is None:
                meta = data.get("metadata", {})
                new_name = meta.get("description", "Imported Preset")
                # Fallback to filename
                if not new_name or new_name == "Imported Preset":
                    new_name = os.path.splitext(os.path.basename(import_path))[0]
            
            # Sanitize and ensure unique
            base_name = self._sanitize_name(new_name)
            name = base_name
            counter = 1
            while os.path.isfile(self.get_preset_path(name)):
                name = f"{base_name} ({counter})"
                counter += 1
            
            # Update metadata
            now = int(time.time())
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["imported_at"] = now
            data["metadata"]["updated_at"] = now
            if "created_at" not in data["metadata"]:
                data["metadata"]["created_at"] = now
            
            file_path = self.get_preset_path(name)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True, name
        except Exception as e:
            print(f"Failed to import preset: {e}")
            return False, str(e)

    ## SERIALIZATION
    def _serialize(self) -> dict:
        tweak_data = {}
        for key, tweak in tweaks.items():
            # PosterBoard is excluded from presets: wallpapers are
            # device-specific and heavy, so they must not travel with a preset.
            if key == TweakID.PosterBoard:
                continue
            try:
                tweak_data[key.name] = self._serialize_tweak(tweak)
            except Exception as e:
                print(f"Failed to serialize tweak {key}: {e}")

        return {
            "tweaks": tweak_data
        }

    def _serialize_tweak(self, tweak) -> dict:
        data = {"type": type(tweak).__name__, "enabled": tweak.enabled}
        if isinstance(tweak, AdvancedPlistTweak):
            data["value"] = tweak.value
        elif isinstance(tweak, BasicPlistTweak):
            data["value"] = tweak.value
        elif isinstance(tweak, PosterboardTweak):
            data["tendies"] = [t.path for t in tweak.tendies]
            data["videoThumbnail"] = tweak.videoThumbnail
            data["videoFile"] = tweak.videoFile
            data["loop_video"] = tweak.loop_video
            data["reverse_video"] = tweak.reverse_video
            data["use_foreground"] = tweak.use_foreground
            data["calculationMode"] = tweak.calculationMode
            data["resetModes"] = tweak.resetModes
            data["bundle_id"] = tweak.bundle_id
            data["saved_items"] = [{"uuid": i.uuid, "extension": i.extension, "set_selected": i.set_selected} for i in tweak.config_manager.saved_items]
        elif isinstance(tweak, TemplatesTweak):
            data["templates"] = [t.path for t in tweak.templates]
        elif isinstance(tweak, StatusBarTweak):
            data["enabled"] = tweak.enabled
            data["silly_mode"] = tweak.setter.silly_mode
            data["override_data"] = base64.b64encode(status_ffi.buffer(tweak.setter.current_overrides)).decode("ascii")
        elif isinstance(tweak, PasscodeThemeTweak):
            data["value"] = tweak.value
            data["language_code"] = tweak.language_code
            data["big_keys"] = tweak.big_keys
            data["current_size"] = tweak.current_size
        # NullifyFileTweak only needs "enabled"
        return data

    ## DESERIALIZATION
    def _apply(self, data: dict) -> bool:
        try:
            # make sure every tweak exists before applying
            self._load_all_tweaks()

            if "tweaks" in data:
                for name, tweak_data in data["tweaks"].items():
                    key = None
                    try:
                        key = TweakID[name]
                    except KeyError:
                        continue
                    if key not in tweaks:
                        continue
                    # PosterBoard is excluded from presets (see _serialize); skip
                    # it on load too so old presets cannot restore wallpapers.
                    if key == TweakID.PosterBoard:
                        continue
                    try:
                        self._apply_tweak(tweaks[key], tweak_data)
                    except Exception as e:
                        print(f"Failed to apply tweak {name}: {e}")

            return True
        except Exception as e:
            print(f"Failed to apply preset: {e}")
            return False

    def _load_all_tweaks(self):
        # idempotent: the loaders return early if the tweaks already exist
        tweak_loader.load_internal()
        tweak_loader.load_springboard()
        tweak_loader.load_liquidglass()
        tweak_loader.load_daemons()

    def _apply_tweak(self, tweak, data: dict):
        if "enabled" in data:
            tweak.enabled = data["enabled"]

        if isinstance(tweak, (BasicPlistTweak, AdvancedPlistTweak)):
            if "value" in data:
                tweak.value = data["value"]
        elif isinstance(tweak, PosterboardTweak):
            self._apply_posterboard(tweak, data)
        elif isinstance(tweak, TemplatesTweak):
            self._apply_templates(tweak, data)
        elif isinstance(tweak, StatusBarTweak):
            self._apply_status_bar(tweak, data)
        elif isinstance(tweak, PasscodeThemeTweak):
            if "value" in data:
                tweak.value = data["value"]
                tweak.enabled = data["value"] not in (None, "")
            if "language_code" in data:
                tweak.language_code = data["language_code"]
            if "big_keys" in data:
                tweak.big_keys = data["big_keys"]
            if "current_size" in data:
                tweak.current_size = data["current_size"]

    def _apply_posterboard(self, tweak: PosterboardTweak, data: dict):
        # replace the tendies
        if "tendies" in data:
            tweak.tendies = []
            for path in data["tendies"]:
                if os.path.isfile(path):
                    try:
                        tweak.add_tendie(path)
                    except Exception as e:
                        print(f"Failed to add tendie: {e}")
        if "videoThumbnail" in data:
            tweak.videoThumbnail = data["videoThumbnail"]
        if "videoFile" in data:
            tweak.videoFile = data["videoFile"]
        if "loop_video" in data:
            tweak.loop_video = data["loop_video"]
        if "reverse_video" in data:
            tweak.reverse_video = data["reverse_video"]
        if "use_foreground" in data:
            tweak.use_foreground = data["use_foreground"]
        if "calculationMode" in data:
            tweak.calculationMode = data["calculationMode"]
        if "resetModes" in data:
            tweak.resetModes = data["resetModes"]
        if "bundle_id" in data:
            tweak.bundle_id = data["bundle_id"]
        if "saved_items" in data:
            try:
                from src.tweaks.posterboard.pb_config_item import PBConfigItem
                tweak.config_manager.saved_items = [
                    PBConfigItem(i["uuid"], i.get("extension", ""), set_selected=i.get("set_selected", False))
                    for i in data["saved_items"]
                ]
            except Exception as e:
                print(f"Failed to restore saved ids: {e}")

    def _apply_templates(self, tweak: TemplatesTweak, data: dict):
        if "templates" in data:
            tweak.templates = []
            for path in data["templates"]:
                if os.path.isfile(path):
                    try:
                        tweak.add_template(path)
                    except Exception as e:
                        print(f"Failed to add template: {e}")

    def _apply_status_bar(self, tweak: StatusBarTweak, data: dict):
        tweak.enabled = data.get("enabled", False)
        tweak.setter.silly_mode = data.get("silly_mode", False)
        if "override_data" in data:
            try:
                raw = base64.b64decode(data["override_data"])
                new_overrides = status_ffi.new("StatusBarOverrideData *")
                struct_size = status_ffi.sizeof(new_overrides[0])
                status_ffi.memmove(new_overrides, raw, min(len(raw), struct_size))
                tweak.setter.apply_changes(new_overrides)
            except Exception as e:
                print(f"Failed to restore status bar: {e}")

