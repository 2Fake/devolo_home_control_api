"""devolo Home Control"""
import threading
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from zeroconf import Zeroconf

from . import __version__
from .backend import MESSAGE_TYPES
from .backend.mprm import Mprm
from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .helper.string import camel_case_to_snake_case
from .helper.uid import (
    get_device_type_from_element_uid,
    get_device_uid_from_element_uid,
    get_device_uid_from_setting_uid,
    get_home_id_from_device_uid,
)
from .mydevolo import Mydevolo
from .properties.binary_sensor_property import BinarySensorProperty
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.humidity_bar_property import HumidityBarProperty
from .properties.multi_level_sensor_property import MultiLevelSensorProperty
from .properties.multi_level_switch_property import MultiLevelSwitchProperty
from .properties.remote_control_property import RemoteControlProperty
from .properties.settings_property import SettingsProperty
from .publisher.publisher import Publisher
from .publisher.updater import Updater


class HomeControl(Mprm):
    """
    Representing object for your Home Control setup. This is more or less the glue between your devolo Home Control Central
    Unit, your devices and their properties.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    :param zeroconf_instance: Zeroconf instance to be potentially reused
    """

    def __init__(self, gateway_id: str, mydevolo_instance: Mydevolo, zeroconf_instance: Optional[Zeroconf] = None) -> None:
        retry = Retry(total=5, backoff_factor=0.1, allowed_methods=("GET", "POST"))
        adapter = HTTPAdapter(max_retries=retry)

        self._mydevolo = mydevolo_instance
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": f"devolo_home_control_api/{__version__}"})
        self._session.mount("http://", adapter)
        self._zeroconf = zeroconf_instance
        self.gateway = Gateway(gateway_id, mydevolo_instance)

        super().__init__()
        self._grouping()

        # Create the initial device dict
        self.devices: Dict[str, Zwave] = {}
        self._inspect_devices(self.get_all_devices())

        self.device_names = {
            f"{device.settings_property['general_device_settings'].name}\\"
            f"{device.settings_property['general_device_settings'].zone}": device.uid
            for device in self.devices.values()
        }

        self.gateway.home_id = get_home_id_from_device_uid(next(iter(self.device_names.values())))

        self.publisher = Publisher(self.devices.keys())

        self.updater = Updater(devices=self.devices, gateway=self.gateway, publisher=self.publisher)
        self.updater.on_device_change = self.device_change

        threading.Thread(target=self.websocket_connect, name=f"{self.__class__.__name__}.websocket_connect").start()
        self.wait_for_websocket_establishment()

    @property
    def binary_sensor_devices(self) -> List[Zwave]:
        """Get all binary sensor devices."""
        return [uid for uid in self.devices.values() if hasattr(uid, "binary_sensor_property")]

    @property
    def binary_switch_devices(self) -> List[Zwave]:
        """Get all binary switch devices."""
        return [uid for uid in self.devices.values() if hasattr(uid, "binary_switch_property")]

    @property
    def blinds_devices(self) -> List[Zwave]:
        """Get all blinds devices."""
        blinds_devices = []
        for device in self.multi_level_switch_devices:
            blinds_devices.extend(
                [
                    self.devices[device.uid]
                    for multi_level_switch_property in device.multi_level_switch_property
                    if multi_level_switch_property.startswith("devolo.Blinds")
                ]
            )
        return blinds_devices

    @property
    def multi_level_sensor_devices(self) -> List[Zwave]:
        """Get all multi level sensor devices."""
        return [uid for uid in self.devices.values() if hasattr(uid, "multi_level_sensor_property")]

    @property
    def multi_level_switch_devices(self) -> List[Zwave]:
        """Get all multi level switch devices. This also includes blinds devices."""
        return [uid for uid in self.devices.values() if hasattr(uid, "multi_level_switch_property")]

    @property
    def remote_control_devices(self) -> List[Zwave]:
        """Get all remote control devices."""
        return [uid for uid in self.devices.values() if hasattr(uid, "remote_control_property")]

    def device_change(self, device_uids: List[str]):
        """
        React on new devices or removed devices. As the Z-Wave controller can only be in inclusion or exclusion mode, we
        assume, that you cannot add and remove devices at the same time. So if the number of devices increases, there is
        a new one and if the number decreases, a device was removed.

        :param device_uids: List of UIDs known by the backend
        """
        if len(device_uids) > len(self.devices):
            devices = [device for device in device_uids if device not in self.devices]
            mode = "add"
            self._inspect_devices([devices[0]])
            self._logger.debug("Device %s added.", devices[0])
        else:
            devices = [device for device in self.devices if device not in device_uids]
            mode = "del"
            self.devices.pop(devices[0])
            self._logger.debug("Device %s removed.", devices[0])
        self.updater.devices = self.devices
        return (devices[0], mode)

    def on_update(self, message: Dict[str, Any]) -> None:
        """
        Initialize steps needed to update properties on a new message.

        :param message: Message because of which we need to update properties
        """
        self.updater.update(message)

    def _binary_sensor(self, uid_info: Dict[str, Any]) -> None:
        """Process BinarySensor properties"""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        if not hasattr(self.devices[device_uid], "binary_sensor_property"):
            self.devices[device_uid].binary_sensor_property = {}
        self._logger.debug("Adding binary sensor property to %s.", device_uid)
        self.devices[device_uid].binary_sensor_property[uid_info["UID"]] = BinarySensorProperty(
            element_uid=uid_info["UID"],
            state=bool(uid_info["properties"]["state"]),
            sensor_type=uid_info["properties"]["sensorType"],
            sub_type=uid_info["properties"]["subType"],
        )

    def _binary_switch(self, uid_info: Dict[str, Any]) -> None:
        """Process BinarySwitch properties."""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        if not hasattr(self.devices[device_uid], "binary_switch_property"):
            self.devices[device_uid].binary_switch_property = {}
        self._logger.debug("Adding binary switch property to %s.", device_uid)
        self.devices[device_uid].binary_switch_property[uid_info["UID"]] = BinarySwitchProperty(
            element_uid=uid_info["UID"],
            setter=self.set_binary_switch,
            state=bool(uid_info["properties"]["state"]),
            enabled=uid_info["properties"]["guiEnabled"],
        )

    def _general_device(self, uid_info: Dict[str, Any]) -> None:
        """Process general device setting (gds) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding general device settings to %s.", device_uid)
        self.devices[device_uid].settings_property["general_device_settings"] = SettingsProperty(
            element_uid=uid_info["UID"],
            setter=self.set_setting,
            events_enabled=uid_info["properties"]["settings"]["eventsEnabled"],
            name=uid_info["properties"]["settings"]["name"],
            zone_id=uid_info["properties"]["settings"]["zoneID"],
            icon=uid_info["properties"]["settings"]["icon"],
            zones=self.gateway.zones,
        )

    def _grouping(self) -> None:
        """Get all zones (also called rooms)."""
        self.gateway.zones = self.get_all_zones()

    def _humidity_bar(self, uid_info: Dict[str, Any]) -> None:
        """
        Process HumidityBarZone and HumidityBarValue properties.

        For whatever reason, the zone and the position within that zone are two different FIs. Nevertheless, it does not make
        sense to separate them. So we fake an FI and a sensorType to combine them together into one object.
        """
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        fake_element_uid = f"devolo.HumidityBar:{uid_info['UID'].split(':', 1)[1]}"
        if not hasattr(self.devices[device_uid], "humidity_bar_property"):
            self.devices[device_uid].humidity_bar_property = {}
        if self.devices[device_uid].humidity_bar_property.get(fake_element_uid) is None:
            self.devices[device_uid].humidity_bar_property[fake_element_uid] = HumidityBarProperty(
                element_uid=fake_element_uid, sensorType="humidityBar"
            )
        if uid_info["properties"]["sensorType"] == "humidityBarZone":
            self._logger.debug("Adding humidity bar zone property to %s.", device_uid)
            self.devices[device_uid].humidity_bar_property[fake_element_uid].zone = uid_info["properties"]["value"]
        elif uid_info["properties"]["sensorType"] == "humidityBarPos":
            self._logger.debug("Adding humidity bar position property to %s.", device_uid)
            self.devices[device_uid].humidity_bar_property[fake_element_uid].value = uid_info["properties"]["value"]

    def _inspect_devices(self, devices: List[str]) -> None:
        """Inspect device properties of given list of devices."""
        devices_properties = self.get_data_from_uid_list(devices)
        for device_properties in devices_properties:
            properties = device_properties["properties"]
            self.devices[device_properties["UID"]] = Zwave(mydevolo_instance=self._mydevolo, **properties)
            self.devices[device_properties["UID"]].settings_property = {}
            threading.Thread(
                target=self.devices[device_properties["UID"]].get_zwave_info,
                name=f"{self.__class__.__name__}.{self.devices[device_properties['UID']].uid}",
            ).start()

        # List comprehension gets the list of uids from every device
        nested_uids_lists = [
            (uid["properties"].get("settingUIDs") + uid["properties"]["elementUIDs"]) for uid in devices_properties
        ]

        # List comprehension gets all uids into one list to make one big call against the mPRM
        uid_list = [uid for sublist in nested_uids_lists for uid in sublist]

        device_properties_list = self.get_data_from_uid_list(uid_list)

        for uid_info in device_properties_list:
            message_type = MESSAGE_TYPES.get(get_device_type_from_element_uid(uid_info["UID"]), "_unknown")
            getattr(self, message_type)(uid_info)
            try:
                uid = self.devices[get_device_uid_from_element_uid(uid_info["UID"])]
            except KeyError:
                uid = self.devices[get_device_uid_from_setting_uid(uid_info["UID"])]
            uid.pending_operations = uid.pending_operations or bool(uid_info["properties"].get("pendingOperations"))

        # Last activity messages sometimes arrive before a device was initialized and therefore need to be handled afterwards.
        for uid_info in device_properties_list:
            if uid_info["UID"].startswith("devolo.LastActivity"):
                self._last_activity(uid_info)

    def _automatic_calibration(self, uid_info: Dict[str, Any]) -> None:
        """Process automatic calibration (acs) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding automatic calibration setting to %s.", device_uid)
        self.devices[device_uid].settings_property["automatic_calibration"] = SettingsProperty(
            element_uid=uid_info["UID"],
            setter=self.set_setting,
            calibration_status=bool(uid_info["properties"]["calibrationStatus"]),
        )

    def _binary_sync(self, uid_info: Dict[str, Any]) -> None:
        """
        Process binary sync setting (bss) properties. Currently only the direction of a shutter in known to be a binary sync
        setting property, so it is named nicely.
        """
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding binary sync setting to %s.", device_uid)
        self.devices[device_uid].settings_property["movement_direction"] = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, inverted=uid_info["properties"]["value"]
        )

    def _binary_async(self, uid_info: Dict[str, Any]) -> None:
        """Process binary async setting (bas) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding binary async settings to %s.", device_uid)
        settings_property = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, value=uid_info["properties"]["value"]
        )

        # The siren needs to be handled differently, as otherwise their binary async setting will not be named nicely
        if self.devices[device_uid].device_model_uid == "devolo.model.Siren":
            self.devices[device_uid].settings_property["muted"] = settings_property
        # As some devices have multiple binary async settings, we use the settings UID split after a '#' as key
        else:
            key = camel_case_to_snake_case(uid_info["UID"].split("#")[-1])
            self.devices[device_uid].settings_property[key] = settings_property

    def _last_activity(self, uid_info: Dict[str, Any]) -> None:
        """
        Process last activity properties. Those don't go into an own property but will be appended to a parent property.
        This parent property is found by string replacement.
        """
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        parent_element_uid = uid_info["UID"].replace("LastActivity", "BinarySensor")
        try:
            self.devices[device_uid].binary_sensor_property[parent_element_uid].last_activity = uid_info["properties"][
                "lastActivityTime"
            ]
        except AttributeError:
            parent_element_uid = uid_info["UID"].replace("LastActivity", "SirenMultiLevelSwitch")
            self.devices[device_uid].multi_level_switch_property[parent_element_uid].last_activity = uid_info["properties"][
                "lastActivityTime"
            ]

    def _led(self, uid_info: Dict[str, Any]) -> None:
        """Process LED information setting (lis) and visual feedback setting (vfs) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding led settings to %s.", device_uid)
        try:
            led_setting = uid_info["properties"]["led"]
        except KeyError:
            led_setting = uid_info["properties"]["feedback"]
        self.devices[device_uid].settings_property["led"] = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, led_setting=led_setting
        )

    def _meter(self, uid_info: Dict[str, Any]) -> None:
        """Process meter properties."""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        if not hasattr(self.devices[device_uid], "consumption_property"):
            self.devices[device_uid].consumption_property = {}
        self._logger.debug("Adding consumption property to %s.", device_uid)
        self.devices[device_uid].consumption_property[uid_info["UID"]] = ConsumptionProperty(
            element_uid=uid_info["UID"],
            current=uid_info["properties"]["currentValue"],
            total=uid_info["properties"]["totalValue"],
            total_since=uid_info["properties"]["sinceTime"],
        )

    def _multilevel_async(self, uid_info: Dict[str, Any]) -> None:
        """Process multilevel async setting (mas) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        try:
            name = camel_case_to_snake_case(uid_info["properties"]["itemId"])
        # The Metering Plug has an multilevel async setting without an ID
        except TypeError:
            if self.devices[device_uid].device_model_uid == "devolo.model.Wall:Plug:Switch:and:Meter":
                name = "flash_mode"
            else:
                raise

        self._logger.debug("Adding %s setting to %s.", name, device_uid)
        self.devices[device_uid].settings_property[name] = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, value=uid_info["properties"]["value"]
        )

    def _multilevel_sync(self, uid_info: Dict[str, Any]) -> None:
        """Process multilevel sync setting (mss) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])

        # The siren needs to be handled differently, as otherwise their multilevel sync setting will not be named nicely.
        if self.devices[device_uid].device_model_uid == "devolo.model.Siren":
            self._logger.debug("Adding tone settings to %s.", device_uid)
            self.devices[device_uid].settings_property["tone"] = SettingsProperty(
                element_uid=uid_info["UID"], setter=self.set_setting, tone=uid_info["properties"]["value"]
            )

        # The shutter needs to be handled differently, as otherwise their multilevel sync setting will not be named nicely.
        elif self.devices[device_uid].device_model_uid in ("devolo.model.OldShutter", "devolo.model.Shutter"):
            self._logger.debug("Adding shutter duration settings to %s.", device_uid)
            self.devices[device_uid].settings_property["shutter_duration"] = SettingsProperty(
                element_uid=uid_info["UID"], setter=self.set_setting, shutter_duration=uid_info["properties"]["value"]
            )

        # Other devices are up to now always motion sensors.
        else:
            self._logger.debug("Adding motion sensitivity settings to %s.", device_uid)
            self.devices[device_uid].settings_property["motion_sensitivity"] = SettingsProperty(
                element_uid=uid_info["UID"], setter=self.set_setting, motion_sensitivity=uid_info["properties"]["value"]
            )

    def _multi_level_sensor(self, uid_info: Dict[str, Any]) -> None:
        """Process multi level sensor properties."""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        if not hasattr(self.devices[device_uid], "multi_level_sensor_property"):
            self.devices[device_uid].multi_level_sensor_property = {}
        self._logger.debug("Adding multi level sensor property %s to %s.", uid_info["UID"], device_uid)
        self.devices[device_uid].multi_level_sensor_property[uid_info["UID"]] = MultiLevelSensorProperty(
            element_uid=uid_info["UID"],
            value=uid_info["properties"]["value"],
            unit=uid_info["properties"]["unit"],
            sensor_type=uid_info["properties"]["sensorType"],
        )

    def _multi_level_switch(self, uid_info: Dict[str, Any]) -> None:
        """Process multi level switch properties."""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        if not hasattr(self.devices[device_uid], "multi_level_switch_property"):
            self.devices[device_uid].multi_level_switch_property = {}
        self._logger.debug("Adding multi level switch property %s to %s.", uid_info["UID"], device_uid)
        self.devices[device_uid].multi_level_switch_property[uid_info["UID"]] = MultiLevelSwitchProperty(
            element_uid=uid_info["UID"],
            setter=self.set_multi_level_switch,
            value=uid_info["properties"]["value"],
            switch_type=uid_info["properties"]["switchType"],
            max=uid_info["properties"]["max"],
            min=uid_info["properties"]["min"],
        )

    def _parameter(self, uid_info: Dict[str, Any]) -> None:
        """Process custom parameter setting (cps) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding parameter settings to %s.", device_uid)
        self.devices[device_uid].settings_property["param_changed"] = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, param_changed=uid_info["properties"]["paramChanged"]
        )

    def _protection(self, uid_info: Dict[str, Any]) -> None:
        """Process protection setting (ps) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding protection settings to %s.", device_uid)
        self.devices[device_uid].settings_property["protection"] = SettingsProperty(
            element_uid=uid_info["UID"],
            setter=self.set_setting,
            local_switching=uid_info["properties"]["localSwitch"],
            remote_switching=uid_info["properties"]["remoteSwitch"],
        )

    def _remote_control(self, uid_info: Dict[str, Any]) -> None:
        """Process remote control properties."""
        device_uid = get_device_uid_from_element_uid(uid_info["UID"])
        self._logger.debug("Adding remote control to %s.", device_uid)
        if not hasattr(self.devices[device_uid], "remote_control_property"):
            self.devices[device_uid].remote_control_property = {}
        self.devices[device_uid].remote_control_property[uid_info["UID"]] = RemoteControlProperty(
            element_uid=uid_info["UID"],
            setter=self.set_remote_control,
            key_count=uid_info["properties"]["keyCount"],
            key_pressed=uid_info["properties"]["keyPressed"],
            type=uid_info["properties"]["type"],
        )

    def _switch_type(self, uid_info: Dict[str, Any]) -> None:
        """
        Process switch type setting (sts) properties. Interestingly, a switch with two buttons reports a switchType of 1 and a
        switch with four buttons reports a switchType of 2. This confusing behavior is corrected by doubling the value.
        """
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding switch type setting to %s.", device_uid)
        self.devices[device_uid].settings_property["switch_type"] = SettingsProperty(
            element_uid=uid_info["UID"], setter=self.set_setting, value=uid_info["properties"]["switchType"] * 2
        )

    def _temperature_report(self, uid_info: Dict[str, Any]) -> None:
        """Process temperature report setting (trs) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info["UID"])
        self._logger.debug("Adding temperature report settings to %s.", device_uid)
        self.devices[device_uid].settings_property["temperature_report"] = SettingsProperty(
            element_uid=uid_info["UID"],
            setter=self.set_setting,
            temp_report=uid_info["properties"]["tempReport"],
            target_temp_report=uid_info["properties"]["targetTempReport"],
        )

    def _unknown(self, uid_info: Dict[str, Any]) -> None:
        """Ignore unknown properties."""
        ignore = ("devolo.SirenBinarySensor", "devolo.SirenMultiLevelSensor", "ss", "mcs")
        if not uid_info["UID"].startswith(ignore):
            self._logger.debug("Found an unexpected element uid: %s", uid_info["UID"])
