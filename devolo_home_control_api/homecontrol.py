import threading
from typing import Optional

import requests

from .backend.mprm import Mprm
from .devices.gateway import Gateway
from .devices.zwave import (Zwave, get_device_type_from_element_uid,
                            get_device_uid_from_element_uid,
                            get_device_uid_from_setting_uid)
from .properties.binary_sensor_property import BinarySensorProperty
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.dewpoint_sensor_property import DewpointSensorProperty
from .properties.humidity_bar_property import HumidityBarProperty
from .properties.mildew_sensor_property import MildewSensorProperty
from .properties.multi_level_sensor_property import MultiLevelSensorProperty
from .properties.settings_property import SettingsProperty
from .properties.voltage_property import VoltageProperty
from .publisher.publisher import Publisher
from .publisher.updater import Updater


class HomeControl(Mprm):
    """
    Representing object for your Home Control setup. This is more or less the glue between your devolo Home Control Central
    Unit, your devices and their properties.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    """

    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._session.url = url

        super().__init__()

        # Create the initial device dict
        self.devices = {}
        self._inspect_devices(self.get_all_devices())

        self.device_names = dict(zip([self.devices.get(device).itemName for device in self.devices],
                                     [self.devices.get(device).uid for device in self.devices]))

        self.publisher = Publisher([device for device in self.devices])

        self.updater = Updater(devices=self.devices, gateway=self._gateway, publisher=self.publisher)
        self.updater.on_device_change = self.device_change

        threading.Thread(target=self.websocket_connect).start()


    @property
    def binary_sensor_devices(self):
        """ Get all binary sensor devices. """
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_sensor_property")]

    @property
    def binary_switch_devices(self) -> list:
        """ Get all binary switch devices. """
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_switch_property")]


    def device_change(self, device_uids: list):
        """
        React on new devices or removed devices. As the Z-Wave controller can only be in inclusion or exclusion mode, we
        assume, that you cannot add and remove devices at the same time. So if the number of devices increases, there is
        a new one and if the number decreases, a device was removed.

        :param device_uids: List of UIDs known by the backend
        """
        if len(device_uids) > len(self.devices):
            new_device = [device for device in device_uids if device not in self.devices]
            self._logger.debug(f"New device found {new_device}")
            self._inspect_devices([new_device[0]])
            self.publisher = Publisher([device for device in self.devices])
        else:
            devices = [device for device in self.devices if device not in device_uids]
            self._logger.debug(f"Device {devices} removed")
            del self.devices[devices[0]]
        self.updater.devices = self.devices

    def on_update(self, message):
        """
        Initialize steps needed to update properties on a new message.

        :param message: Message because of which we need to update properties
        """
        self.updater.update(message)


    def _binary_sensor(self, uid_info: dict):
        """ Process BinarySensor properties"""
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "binary_sensor_property"):
            self.devices[device_uid].binary_sensor_property = {}
        self._logger.debug(f"Adding binary sensor property to {device_uid}.")
        self.devices[device_uid].binary_sensor_property[uid_info.get("UID")] = \
            BinarySensorProperty(session=self._session,
                                 gateway=self._gateway,
                                 element_uid=uid_info.get("UID"),
                                 state=bool(uid_info.get("properties").get("state")),
                                 sensor_type=uid_info.get("properties").get("sensorType"),
                                 sub_type=uid_info.get("properties").get("subType"))

    def _binary_switch(self, uid_info: dict):
        """ Process BinarySwitch properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "binary_switch_property"):
            self.devices[device_uid].binary_switch_property = {}
        self._logger.debug(f"Adding binary switch property to {device_uid}.")
        self.devices[device_uid].binary_switch_property[uid_info.get("UID")] = \
            BinarySwitchProperty(session=self._session,
                                 gateway=self._gateway,
                                 element_uid=uid_info.get("UID"),
                                 state=bool(uid_info.get("properties").get("state")))

    def _dewpoint(self, uid_info: dict):
        """ Process dewpoint sensor properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "dewpoint_sensor_property"):
            self.devices[device_uid].dewpoint_sensor_property = {}
        self._logger.debug(f"Adding dewpoint sensor property to {device_uid}.")
        self.devices[device_uid].dewpoint_sensor_property[uid_info.get("UID")] = \
            DewpointSensorProperty(session=self._session,
                                   gateway=self._gateway,
                                   element_uid=uid_info.get("UID"),
                                   value=uid_info.get("properties").get("value"),
                                   sensor_type=uid_info.get("properties").get("sensorType"))

    def _general_device(self, uid_info: dict):
        """ Process general device setting (gds) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding general device settings to {device_uid}.")
        self.devices[device_uid]. \
            settings_property["general_device_settings"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get("UID"),
                             events_enabled=uid_info.get("properties").get("settings").get("eventsEnabled"),
                             name=uid_info.get("properties").get("settings").get("name"),
                             zone_id=uid_info.get("properties").get("settings").get("zoneID"),
                             icon=uid_info.get("properties").get("settings").get("icon"))

    def _humidity_bar(self, uid_info: dict):
        """
        Process HumidityBarZone and HumidityBarValue properties.

        For whatever reason, the zone and the position within that zone are two different FIs. Nevertheless, it does not make
        sense to separate them. So we fake an FI and a sensorType to combine them together into one object.
        """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        fake_element_uid = f'devolo.HumidityBar:{uid_info.get("UID").split(":", 1)[1]}'
        if not hasattr(self.devices[device_uid], "humidity_bar_property"):
            self.devices[device_uid].humidity_bar_property = {}
        if self.devices[device_uid].humidity_bar_property.get(fake_element_uid) is None:
            self.devices[device_uid].humidity_bar_property[fake_element_uid] = \
                HumidityBarProperty(session=self._session,
                                    gateway=self._gateway,
                                    element_uid=fake_element_uid,
                                    sensorType="humidityBar")
        if uid_info.get("properties").get("sensorType") == "humidityBarZone":
            self._logger.debug(f"Adding humidity bar zone property to {device_uid}.")
            self.devices[device_uid].humidity_bar_property[fake_element_uid].zone = uid_info.get("properties").get("value")
        elif uid_info.get("properties").get("sensorType") == "humidityBarPos":
            self._logger.debug(f"Adding humidity bar position property to {device_uid}.")
            self.devices[device_uid].humidity_bar_property[fake_element_uid].value = uid_info.get("properties").get("value")

    def _inspect_devices(self, devices: list):
        """ Inspect device properties of given list of devices. """
        devices_properties = self.get_data_from_uid_list(devices)
        for device_properties in devices_properties:
            properties = device_properties.get("properties")
            self.devices[device_properties.get("UID")] = Zwave(**properties)
            self.devices[device_properties.get("UID")].settings_property = {}
            threading.Thread(target=self.devices[device_properties.get("UID")].get_zwave_info).start()

        elements = {"devolo.BinarySensor": self._binary_sensor,
                    "devolo.BinarySwitch": self._binary_switch,
                    "devolo.DewpointSensor": self._dewpoint,
                    "devolo.HumidityBarValue": self._humidity_bar,
                    "devolo.HumidityBarZone": self._humidity_bar,
                    "devolo.LastActivity": self._last_activity,
                    "devolo.Meter": self._meter,
                    "devolo.MildewSensor": self._mildew,
                    "devolo.MultiLevelSensor": self._multi_level_sensor,
                    "devolo.VoltageMultiLevelSensor": self._voltage_multi_level_sensor,
                    "lis.hdm": self._led,
                    "gds.hdm": self._general_device,
                    "cps.hdm": self._parameter,
                    "mss.hdm": self._motion_sensitivity,
                    "ps.hdm": self._protection,
                    "trs.hdm": self._temperature_report,
                    "vfs.hdm": self._led
                    }

        # List comprehension gets the list of uids from every device
        nested_uids_lists = [(uid.get("properties").get('settingUIDs')
                              + uid.get("properties").get("elementUIDs"))
                             for uid in devices_properties]

        # List comprehension gets all uids into one list to make one big call against the mPRM
        uid_list = [uid for sublist in nested_uids_lists for uid in sublist]

        for uid_info in self.get_data_from_uid_list(uid_list):
            if uid_info.get("UID") is not None:
                elements.get(get_device_type_from_element_uid(uid_info.get("UID")), self._unknown)(uid_info)

    def _last_activity(self, uid_info: dict):
        """
        Process last activity properties. Those don't go into an own property but will be appended to a parent property.
        This parent property is found by string replacement.
        """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if uid_info.get("properties").get("lastActivityTime") != -1 and \
                hasattr(self.devices[device_uid], "binary_sensor_property"):
            parent_element_uid = uid_info.get("UID").replace("LastActivity", "BinarySensor")
            self.devices[device_uid].binary_sensor_property[parent_element_uid].last_activity = \
                uid_info.get("properties").get("lastActivityTime")

    def _led(self, uid_info: dict):
        """ Process LED information setting (lis) and visual feedback setting (vfs) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding led settings to {device_uid}.")
        if uid_info.get("properties").get("led"):
            led_setting = uid_info.get("properties").get("led")
        else:
            led_setting = uid_info.get("properties").get("feedback")
        self.devices[device_uid].settings_property["led"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get("UID"),
                             led_setting=led_setting)

    def _meter(self, uid_info: dict):
        """ Process meter properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "consumption_property"):
            self.devices[device_uid].consumption_property = {}
        self._logger.debug(f"Adding consumption property to {device_uid}.")
        self.devices[device_uid].consumption_property[uid_info.get("UID")] = \
            ConsumptionProperty(session=self._session,
                                gateway=self._gateway,
                                element_uid=uid_info.get("UID"),
                                current=uid_info.get("properties").get("currentValue"),
                                total=uid_info.get("properties").get("totalValue"),
                                total_since=uid_info.get("properties").get("sinceTime"))

    def _mildew(self, uid_info: dict):
        """ Process mildew sensor properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "mildew_sensor_property"):
            self.devices[device_uid].mildew_sensor_property = {}
        self._logger.debug(f"Adding mildew sensor property to {device_uid}.")
        self.devices[device_uid].mildew_sensor_property[uid_info.get("UID")] = \
            MildewSensorProperty(session=self._session,
                                 gateway=self._gateway,
                                 element_uid=uid_info.get("UID"),
                                 state=bool(uid_info.get("properties").get("state")),
                                 sensor_type=uid_info.get("properties").get("sensorType"))

    def _motion_sensitivity(self, uid_info: dict):
        """ Process motion sensitivity setting (mss) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding motion sensitiviy settings to {device_uid}.")
        self.devices[device_uid].settings_property["motion_sensitivity"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get("UID"),
                             motion_sensitivity=uid_info.get("properties").get("value"),
                             target_motion_sensitivity=uid_info.get("properties").get("targetValue"))

    def _multi_level_sensor(self, uid_info: dict):
        """ Process multi level sensor properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "multi_level_sensor_property"):
            self.devices[device_uid].multi_level_sensor_property = {}
        self._logger.debug(f"Adding multi_level_sensor property {uid_info.get('UID')} to {device_uid}.")
        self.devices[device_uid].multi_level_sensor_property[uid_info.get("UID")] = \
            MultiLevelSensorProperty(session=self._session,
                                     gateway=self._gateway,
                                     element_uid=uid_info.get("UID"),
                                     value=uid_info.get("properties").get("value"),
                                     unit=uid_info.get("properties").get("unit"),
                                     sensor_type=uid_info.get("properties").get("sensorType"))

    def _parameter(self, uid_info: dict):
        """ Process custom parameter setting (cps) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding parameter settings to {device_uid}.")
        self.devices[device_uid].settings_property["param_changed"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get('UID'),
                             param_changed=uid_info.get('properties').get("paramChanged"))

    def _protection(self, uid_info: dict):
        """ Process protection setting (ps) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding protection settings to {device_uid}.")
        self.devices[device_uid].settings_property["protection"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get('UID'),
                             local_switching=uid_info.get("properties").get("localSwitch"),
                             remote_switching=uid_info.get("properties").get("remoteSwitch"))

    def _temperature_report(self, uid_info: dict):
        """ Process temperature report setting (trs) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info.get("UID"))
        self._logger.debug(f"Adding temperature report settings to {device_uid}.")
        self.devices[device_uid].settings_property["temperature_report"] = \
            SettingsProperty(session=self._session,
                             gateway=self._gateway,
                             element_uid=uid_info.get('UID'),
                             temp_report=uid_info.get("properties").get("tempReport"),
                             target_temp_report=uid_info.get("properties").get("targetTempReport"))

    def _unknown(self, uid_info: dict):
        """ Ignore unknown properties. """
        self._logger.debug(f"Found an unexpected element uid: {uid_info.get('UID')}")

    def _voltage_multi_level_sensor(self, uid_info: dict):
        """ Process VoltageMultiLevelSensor properties. """
        device_uid = get_device_uid_from_element_uid(uid_info.get("UID"))
        if not hasattr(self.devices[device_uid], "voltage_property"):
            self.devices[device_uid].voltage_property = {}
        self._logger.debug(f"Adding voltage property to {device_uid}.")
        self.devices[device_uid].voltage_property[uid_info.get("UID")] = \
            VoltageProperty(session=self._session,
                            gateway=self._gateway,
                            element_uid=uid_info.get("UID"),
                            current=uid_info.get("properties").get("value"),
                            sensor_type=uid_info.get("properties").get("sensorType"))


def get_sub_device_uid_from_element_uid(element_uid: str) -> Optional[int]:
    """
    Return the sub device uid of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])
