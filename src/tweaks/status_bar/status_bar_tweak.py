from .status_setter import Setter, StatusBarItem
from ..tweak_classes import Tweak
from src.devicemanagement.constants import Version

from cffi import FFI
ffi = FFI()

class StatusBarTweak(Tweak):
    def __init__(self):
        super().__init__(key=None)
        self.setter = Setter()

    # iOS 27: the status bar is Speakeasy, a SpringBoard feature flag — 
    # but writing the SpeakeasyNewStatusBar flag fails due to no write permissions.
    # The feature is disabled on iOS 27+.
    def apply_tweak(self, flag_plist: dict = None, version: str = "27.0") -> dict:
        if not self.enabled or flag_plist is None:
            return flag_plist
        if Version(version) >= Version("27.0"):
            return flag_plist
        category = flag_plist.setdefault("SpringBoard", {})
        category["SpeakeasyNewStatusBar"] = self.get_speakeasy_payload()
        return flag_plist

    def get_speakeasy_payload(self) -> dict:
        """Translate the StatusBarOverrideData struct into the Speakeasy flag value.

        TODO(ios27): the actual dict schema is not confirmed — the keys below
        are guesses mirroring the classic statusBarOverrides plist format
        (override* bools + nested values dict). They must be verified on-device
        once the real keys are extracted from SpringBoard (speakeasy strings
        in the dyld shared cache).
        """
        overrides = self.setter.get_overrides()
        if self.setter.silly_mode:
            # mirror Setter.get_data(): turn every non-overridden item on
            overrides = ffi.new("StatusBarOverrideData *")
            ffi.memmove(overrides, self.setter.get_overrides(), ffi.sizeof(self.setter.get_overrides()))
            for i in range(46):
                if overrides.overrideItemIsEnabled[i] == 0:
                    overrides.overrideItemIsEnabled[i] = 1
                    overrides.values.itemIsEnabled[i] = 1

        override: dict = {}
        values: dict = {}
        if any(overrides.overrideItemIsEnabled[i] != 0 for i in range(46)):
            override["overrideItemIsEnabled"] = [
                int(overrides.overrideItemIsEnabled[i]) for i in range(46)]
            values["itemIsEnabled"] = [
                int(overrides.values.itemIsEnabled[i]) for i in range(46)]
        if overrides.overrideTimeString != 0:
            override["overrideTimeString"] = 1
            values["timeString"] = ffi.string(overrides.values.timeString).decode()
        if overrides.overrideDateString != 0:
            override["overrideDateString"] = 1
            values["dateString"] = ffi.string(overrides.values.dateString).decode()
        if overrides.overrideGSMSignalStrengthBars != 0:
            override["overrideGSMSignalStrengthBars"] = 1
            values["GSMSignalStrengthBars"] = overrides.values.GSMSignalStrengthBars
        if overrides.overrideSecondaryGSMSignalStrengthBars != 0:
            override["overrideSecondaryGSMSignalStrengthBars"] = 1
            values["secondaryGSMSignalStrengthBars"] = overrides.values.secondaryGSMSignalStrengthBars
        if overrides.overrideWifiSignalStrengthBars != 0:
            override["overrideWifiSignalStrengthBars"] = 1
            values["wifiSignalStrengthBars"] = overrides.values.wifiSignalStrengthBars
        if overrides.overrideServiceString != 0:
            override["overrideServiceString"] = 1
            values["serviceString"] = ffi.string(overrides.values.serviceString).decode()
        if overrides.overrideSecondaryServiceString != 0:
            override["overrideSecondaryServiceString"] = 1
            values["secondaryServiceString"] = ffi.string(overrides.values.secondaryServiceString).decode()
        if overrides.overridePrimaryServiceBadgeString != 0:
            override["overridePrimaryServiceBadgeString"] = 1
            values["primaryServiceBadgeString"] = ffi.string(overrides.values.primaryServiceBadgeString).decode()
        if overrides.overrideSecondaryServiceBadgeString != 0:
            override["overrideSecondaryServiceBadgeString"] = 1
            values["secondaryServiceBadgeString"] = ffi.string(overrides.values.secondaryServiceBadgeString).decode()
        if overrides.overrideDataNetworkType != 0:
            override["overrideDataNetworkType"] = 1
            values["dataNetworkType"] = overrides.values.dataNetworkType
        if overrides.overrideSecondaryDataNetworkType != 0:
            override["overrideSecondaryDataNetworkType"] = 1
            values["secondaryDataNetworkType"] = overrides.values.secondaryDataNetworkType
        if overrides.overrideBatteryCapacity != 0:
            override["overrideBatteryCapacity"] = 1
            values["batteryCapacity"] = overrides.values.batteryCapacity
        if overrides.overrideBatteryDetailString != 0:
            override["overrideBatteryDetailString"] = 1
            values["batteryDetailString"] = ffi.string(overrides.values.batteryDetailString).decode()
        if overrides.overrideBreadcrumb != 0:
            override["overrideBreadcrumb"] = 1
            values["breadcrumbTitle"] = ffi.string(overrides.values.breadcrumbTitle).decode()
        if overrides.overrideDisplayRawGSMSignal != 0:
            override["overrideDisplayRawGSMSignal"] = 1
            values["displayRawGSMSignal"] = overrides.values.displayRawGSMSignal
        if overrides.overrideDisplayRawWifiSignal != 0:
            override["overrideDisplayRawWifiSignal"] = 1
            values["displayRawWifiSignal"] = overrides.values.displayRawWifiSignal

        payload: dict = {"Enabled": True}
        payload.update(override)
        if values:
            payload["values"] = values
        return payload

        
    ### PRIMARY CARRIER
    # CELLULAR SERVICE
    def is_cellular_service_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideItemIsEnabled[StatusBarItem.CellularServiceStatusBarItem.value] == 1
    def get_cellular_service_override(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.values.itemIsEnabled[StatusBarItem.CellularServiceStatusBarItem.value] == 1
    def set_cellular_service(self, shown: bool) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.CellularServiceStatusBarItem.value] = 1
        overrides.values.itemIsEnabled[StatusBarItem.CellularServiceStatusBarItem.value] = 1 if shown else 0
        self.setter.apply_changes(overrides)
    def unset_cellular_service(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.CellularServiceStatusBarItem.value] = 0
        self.setter.apply_changes(overrides)
            
    # SERVICE STRING
    def is_carrier_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideServiceString == 1
    def get_carrier_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.serviceString).decode()
    def set_carrier_override(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideServiceString = 1
        truncated = text[:100]
        overrides.values.serviceString = truncated.encode()
        overrides.values.serviceCrossfadeString = truncated.encode()
        self.setter.apply_changes(overrides)
    def unset_carrier_override(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideServiceString = 0
        self.setter.apply_changes(overrides)

    # SERVICE BADGE
    def is_primary_service_badge_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overridePrimaryServiceBadgeString == 1
    def get_primary_service_badge_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.primaryServiceBadgeString).decode()
    def set_primary_service_badge(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overridePrimaryServiceBadgeString = 1
        overrides.values.primaryServiceBadgeString = text[:100].encode()
        self.setter.apply_changes(overrides)
    def unset_primary_service_badge(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overridePrimaryServiceBadgeString = 0
        self.setter.apply_changes(overrides)

    # DATA NETWORK TYPE
    def is_data_network_type_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideDataNetworkType == 1
    def get_data_network_type_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.dataNetworkType
    def set_data_network_type(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideDataNetworkType = 1
        overrides.values.dataNetworkType = id
        self.setter.apply_changes(overrides)
    def unset_data_network_type(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideDataNetworkType = 0
        self.setter.apply_changes(overrides)

    # GSM SIGNAL BARS
    def is_gsm_signal_strength_bars_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideGSMSignalStrengthBars == 1
    def get_gsm_signal_strength_bars_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.GSMSignalStrengthBars
    def set_gsm_signal_strength_bars(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.CellularSignalStrengthStatusBarItem.value] = 1
        overrides.values.itemIsEnabled[StatusBarItem.CellularSignalStrengthStatusBarItem.value] = 1
        overrides.overrideGSMSignalStrengthBars = 1
        overrides.values.GSMSignalStrengthBars = id
        self.setter.apply_changes(overrides)
    def unset_gsm_signal_strength_bars(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.CellularSignalStrengthStatusBarItem.value] = 0
        overrides.overrideGSMSignalStrengthBars = 0
        self.setter.apply_changes(overrides)


    ### SECONDARY CARRIER
    # CELLULAR SERVICE
    def is_secondary_cellular_service_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideItemIsEnabled[StatusBarItem.SecondaryCellularServiceStatusBarItem.value] == 1
    def get_secondary_cellular_service_override(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.values.itemIsEnabled[StatusBarItem.SecondaryCellularServiceStatusBarItem.value] == 1
    def set_secondary_cellular_service(self, shown: bool) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.SecondaryCellularServiceStatusBarItem.value] = 1
        overrides.values.itemIsEnabled[StatusBarItem.SecondaryCellularServiceStatusBarItem.value] = 1 if shown else 0
        overrides.overrideSecondaryCellularConfigured = 1
        overrides.values.secondaryCellularConfigured = 1 if shown else 0
        self.setter.apply_changes(overrides)
    def unset_secondary_cellular_service(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.SecondaryCellularServiceStatusBarItem.value] = 0
        overrides.overrideSecondaryCellularConfigured = 0
        self.setter.apply_changes(overrides)
            
    # SERVICE STRING
    def is_secondary_carrier_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideSecondaryServiceString == 1
    def get_secondary_carrier_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.secondaryServiceString).decode()
    def set_secondary_carrier_override(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryServiceString = 1
        truncated = text[:100]
        overrides.values.secondaryServiceString = truncated.encode()
        overrides.values.secondaryServiceCrossfadeString = truncated.encode()
        self.setter.apply_changes(overrides)
    def unset_secondary_carrier_override(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryServiceString = 0
        self.setter.apply_changes(overrides)

    # SERVICE BADGE
    def is_secondary_service_badge_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideSecondaryServiceBadgeString == 1
    def get_secondary_service_badge_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.secondaryServiceBadgeString).decode()
    def set_secondary_service_badge(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryServiceBadgeString = 1
        overrides.values.secondaryServiceBadgeString = text[:100].encode()
        self.setter.apply_changes(overrides)
    def unset_secondary_service_badge(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryServiceBadgeString = 0
        self.setter.apply_changes(overrides)

    # DATA NETWORK TYPE
    def is_secondary_data_network_type_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideSecondaryDataNetworkType == 1
    def get_secondary_data_network_type_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.secondaryDataNetworkType
    def set_secondary_data_network_type(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryDataNetworkType = 1
        overrides.values.secondaryDataNetworkType = id
        self.setter.apply_changes(overrides)
    def unset_secondary_data_network_type(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideSecondaryDataNetworkType = 0
        self.setter.apply_changes(overrides)

    # GSM SIGNAL BARS
    def is_secondary_gsm_signal_strength_bars_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideSecondaryGSMSignalStrengthBars == 1
    def get_secondary_gsm_signal_strength_bars_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.secondaryGSMSignalStrengthBars
    def set_secondary_gsm_signal_strength_bars(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.SecondaryCellularSignalStrengthStatusBarItem.value] = 1
        overrides.values.itemIsEnabled[StatusBarItem.SecondaryCellularSignalStrengthStatusBarItem.value] = 1
        overrides.overrideSecondaryGSMSignalStrengthBars = 1
        overrides.values.secondaryGSMSignalStrengthBars = id
        self.setter.apply_changes(overrides)
    def unset_secondary_gsm_signal_strength_bars(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[StatusBarItem.SecondaryCellularSignalStrengthStatusBarItem.value] = 0
        overrides.overrideSecondaryGSMSignalStrengthBars = 0
        self.setter.apply_changes(overrides)


    ### MISC TEXT INPUTS
    # TIME STRING
    def is_time_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideTimeString == 1
    def get_time_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.timeString).decode()
    def set_time(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideTimeString = 1
        overrides.values.timeString = text[:64].encode()
        self.setter.apply_changes(overrides)
    def unset_time(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideTimeString = 0
        self.setter.apply_changes(overrides)

    # DATE STRING
    def is_date_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideDateString == 1
    def get_date_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.dateString).decode()
    def set_date(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideDateString = 1
        overrides.values.dateString = text[:256].encode()
        self.setter.apply_changes(overrides)
    def unset_date(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideDateString = 0
        self.setter.apply_changes(overrides)

    # BREADCRUMB STRING
    def is_crumb_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideBreadcrumb == 1
    def get_crumb_override(self) -> str:
        overrides = self.setter.get_overrides()
        text: str = ffi.string(overrides.values.breadcrumbTitle).decode()
        if len(text) > 1:
            return text[:len(text) - 4]
        return ""
    def set_crumb(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBreadcrumb = 1
        new_crumb = ""
        if text != "":
            new_crumb: str = text[:254] + " ▶"
        overrides.values.breadcrumbTitle = new_crumb.encode()
        self.setter.apply_changes(overrides)
    def unset_crumb(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBreadcrumb = 0
        overrides.values.breadcrumbTitle = "".encode()
        self.setter.apply_changes(overrides)

    # BATTERY DETAIL STRING
    def is_battery_detail_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideBatteryDetailString == 1
    def get_battery_detail_override(self) -> str:
        overrides = self.setter.get_overrides()
        return ffi.string(overrides.values.batteryDetailString).decode()
    def set_battery_detail(self, text: str) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBatteryDetailString = 1
        overrides.values.batteryDetailString = text[:150].encode()
        self.setter.apply_changes(overrides)
    def unset_battery_detail(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBatteryDetailString = 0
        self.setter.apply_changes(overrides)


    ## MISC SLIDER INPUTS
    # BATTERY CAPACITY
    def is_battery_capacity_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideBatteryCapacity == 1
    def get_battery_capacity_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.batteryCapacity
    def set_battery_capacity(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBatteryCapacity = 1
        overrides.values.batteryCapacity = id
        self.setter.apply_changes(overrides)
    def unset_battery_capacity(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideBatteryCapacity = 0
        self.setter.apply_changes(overrides)

    # WIFI SIGNAL STRENGTH
    def is_wifi_signal_strength_bars_overridden(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideWifiSignalStrengthBars == 1
    def get_wifi_signal_strength_bars_override(self) -> int:
        overrides = self.setter.get_overrides()
        return overrides.values.wifiSignalStrengthBars
    def set_wifi_signal_strength_bars(self, id: int) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideWifiSignalStrengthBars = 1
        overrides.values.wifiSignalStrengthBars = id
        self.setter.apply_changes(overrides)
    def unset_wifi_signal_strength_bars(self) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideWifiSignalStrengthBars = 0
        self.setter.apply_changes(overrides)


    ## RAW SIGNAL STRENGTH TOGGLES
    # WIFI
    def is_raw_wifi_signal_shown(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideDisplayRawWifiSignal == 1
    def show_raw_wifi_signal(self, shown: bool) -> None:
        overrides = self.setter.get_overrides()
        if shown:
            overrides.overrideDisplayRawWifiSignal = 1
            overrides.values.displayRawWifiSignal = 1
        else:
            overrides.overrideDisplayRawWifiSignal = 0
        self.setter.apply_changes(overrides)
    # GSM
    def is_raw_gsm_signal_shown(self) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideDisplayRawGSMSignal == 1
    def show_raw_gsm_signal(self, shown: bool) -> None:
        overrides = self.setter.get_overrides()
        if shown:
            overrides.overrideDisplayRawGSMSignal = 1
            overrides.values.displayRawGSMSignal = 1
        else:
            overrides.overrideDisplayRawGSMSignal = 0
        self.setter.apply_changes(overrides)

    ## RADIO BUTTONS
    def is_item_overridden(self, item: StatusBarItem) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.overrideItemIsEnabled[item.value] == 1
    def get_item_override(self, item: StatusBarItem) -> bool:
        overrides = self.setter.get_overrides()
        return overrides.values.itemIsEnabled[item.value] == 1
    def set_item_override(self, item: StatusBarItem, shown: bool) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[item.value] = 1
        overrides.values.itemIsEnabled[item.value] = 1 if shown else 0
        self.setter.apply_changes(overrides)
    def unset_item_override(self, item: StatusBarItem) -> None:
        overrides = self.setter.get_overrides()
        overrides.overrideItemIsEnabled[item.value] = 0
        self.setter.apply_changes(overrides)


    def is_silly_mode_enabled(self) -> bool:
        return self.setter.silly_mode
    def toggle_silly_mode(self, value: bool) -> None:
        self.setter.silly_mode = value
