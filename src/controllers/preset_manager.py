import base64
import json
import os

from PySide6.QtCore import QStandardPaths, QCoreApplication

from src.tweaks.tweak_names import TweakID
from src.tweaks import tweak_loader
from src.tweaks.tweaks import tweaks
from src.tweaks.tweak_classes import (
    MobileGestaltTweak, MobileGestaltMultiTweak, MobileGestaltPickerTweak,
    MobileGestaltCacheDataTweak, RdarFixTweak, FeatureFlagTweak,
    BasicPlistTweak, AdvancedPlistTweak, NullifyFileTweak,
)
from src.tweaks.eligibility_tweak import EligibilityTweak, AITweak, BookRestoreFileTweak
from src.tweaks.custom_gestalt_tweaks import CustomGestaltTweaks, ValueType
from src.tweaks.posterboard.posterboard_tweak import PosterboardTweak
from src.tweaks.posterboard.template_options.templates_tweak import TemplatesTweak
from src.tweaks.status_bar.status_bar_tweak import StatusBarTweak
from src.tweaks.passcode_theme_tweak import PasscodeThemeTweak
from src.tweaks.status_bar.status_bar_c.status_setter import ffi as status_ffi

PRESETS_DIR_NAME = "Presets"

class PresetManager:
    def __init__(self):
        self.presets_dir = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.AppDataLocation),
            PRESETS_DIR_NAME
        )
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

    def save_preset(self, name: str) -> bool:
        data = self._serialize()
        if data is None:
            return False
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

    ## SERIALIZATION
    def _serialize(self) -> dict:
        tweak_data = {}
        for key, tweak in tweaks.items():
            try:
                tweak_data[key.name] = self._serialize_tweak(tweak)
            except Exception as e:
                print(f"Failed to serialize tweak {key}: {e}")

        # custom gestalt tweaks
        custom_gestalt = []
        for item in CustomGestaltTweaks.custom_tweaks:
            if item.tweak is None:
                custom_gestalt.append({
                    "key": "", "value": "", "value_type": item.value_type.value,
                    "deactivated": item.deactivated
                })
            else:
                custom_gestalt.append({
                    "key": item.tweak.key,
                    "value": item.tweak.value,
                    "value_type": item.value_type.value,
                    "deactivated": item.deactivated
                })

        return {
            "tweaks": tweak_data,
            "custom_gestalt": custom_gestalt
        }

    def _serialize_tweak(self, tweak) -> dict:
        data = {"type": type(tweak).__name__, "enabled": tweak.enabled}
        if isinstance(tweak, MobileGestaltPickerTweak):
            data["key"] = tweak.key
            data["subkey"] = tweak.subkey
            data["values"] = tweak.value
            data["selected_option"] = tweak.selected_option
        elif isinstance(tweak, MobileGestaltMultiTweak):
            data["keyValues"] = tweak.keyValues
        elif isinstance(tweak, MobileGestaltCacheDataTweak):
            data["slice_start"] = tweak.slice_start
            data["slice_len"] = tweak.slice_len
        elif isinstance(tweak, MobileGestaltTweak):
            data["key"] = tweak.key
            data["subkey"] = tweak.subkey
            data["value"] = tweak.value
        elif isinstance(tweak, RdarFixTweak):
            data["mode"] = tweak.mode
            data["di_type"] = tweak.di_type
        elif isinstance(tweak, EligibilityTweak):
            data["code"] = tweak.code
            data["method"] = tweak.method
        elif isinstance(tweak, AITweak):
            data["value"] = tweak.value
        elif isinstance(tweak, AdvancedPlistTweak):
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
        # FeatureFlagTweak, NullifyFileTweak, BookRestoreFileTweak only need "enabled"
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
                    try:
                        self._apply_tweak(tweaks[key], tweak_data)
                    except Exception as e:
                        print(f"Failed to apply tweak {name}: {e}")

            if "custom_gestalt" in data:
                self._apply_custom_gestalt(data["custom_gestalt"])

            return True
        except Exception as e:
            print(f"Failed to apply preset: {e}")
            return False

    def _load_all_tweaks(self):
        # idempotent: the loaders return early if the tweaks already exist
        tweak_loader.load_mobilegestalt(None)
        tweak_loader.load_eligibility(None)
        tweak_loader.load_featureflags()
        tweak_loader.load_internal()
        tweak_loader.load_springboard()
        tweak_loader.load_liquidglass()
        tweak_loader.load_daemons()

    def _apply_tweak(self, tweak, data: dict):
        if "enabled" in data:
            tweak.enabled = data["enabled"]

        if isinstance(tweak, MobileGestaltPickerTweak):
            if "values" in data:
                tweak.value = data["values"]
            if "selected_option" in data:
                tweak.selected_option = data["selected_option"]
        elif isinstance(tweak, MobileGestaltMultiTweak):
            if "keyValues" in data:
                tweak.keyValues = data["keyValues"]
        elif isinstance(tweak, MobileGestaltCacheDataTweak):
            if "slice_start" in data:
                tweak.slice_start = data["slice_start"]
            if "slice_len" in data:
                tweak.slice_len = data["slice_len"]
        elif isinstance(tweak, MobileGestaltTweak):
            if "value" in data:
                tweak.value = data["value"]
        elif isinstance(tweak, RdarFixTweak):
            if "mode" in data:
                tweak.mode = data["mode"]
            if "di_type" in data:
                tweak.di_type = data["di_type"]
        elif isinstance(tweak, EligibilityTweak):
            if "code" in data:
                tweak.code = data["code"]
            if "method" in data:
                tweak.method = data["method"]
        elif isinstance(tweak, AITweak):
            if "value" in data:
                tweak.value = data["value"]
        elif isinstance(tweak, (BasicPlistTweak, AdvancedPlistTweak)):
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

    def _apply_custom_gestalt(self, items: list[dict]):
        CustomGestaltTweaks.custom_tweaks = []
        for item in items:
            value_type = ValueType(item.get("value_type", ValueType.Integer.value))
            if item.get("deactivated", False):
                CustomGestaltTweaks.create_deactivated(value_type)
                continue
            try:
                CustomGestaltTweaks.create_tweak(
                    key=item.get("key", ""),
                    value=item.get("value", ""),
                    value_type=value_type
                )
            except Exception as e:
                print(f"Failed to restore custom gestalt tweak: {e}")
