import logging
import threading
from typing import Optional

import requests

from .backend.mprm_websocket import MprmWebsocket
from .devices.gateway import Gateway
from .devices.zwave import Zwave, get_device_type_from_element_uid, get_device_uid_from_setting_uid, \
    get_device_uid_from_element_uid
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.settings_property import SettingsProperty
from .properties.voltage_property import VoltageProperty
from .publisher.publisher import Publisher
from .publisher.updater import Updater


class HomeControl:
    """
    Representing object for your Home Control setup. This is more or less the glue between your devolo Home Control Central
    Unit, your devices and their properties.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    """

    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()

        self.mprm = MprmWebsocket(gateway_id=gateway_id, url=url)
        self.mprm.on_update = self.update
        self.mprm.detect_gateway_in_lan()
        self.mprm.create_connection()

        # Create the initial device dict
        self.devices = {}
        self._inspect_devices(self.mprm.all_devices)

        self.device_names = dict(zip([self.devices.get(device).itemName for device in self.devices],
                                     [self.devices.get(device).uid for device in self.devices]))

        self.create_pub()

        self.updater = Updater(devices=self.devices, gateway=self._gateway, publisher=self.mprm.publisher)
        self.updater.on_device_change = self.device_change

        threading.Thread(target=self.mprm.websocket_connection).start()


    @property
    def binary_switch_devices(self) -> list:
        """ Get all binary switch devices. """
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_switch_property")]

    @property
    def publisher(self) -> Optional[Publisher]:
        """ Get all publisher. """
        return self.mprm.publisher


    def create_pub(self):
        """ Create a publisher for every device. """
        self.mprm.publisher = Publisher([device for device in self.devices])

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
            self.mprm.publisher = Publisher([device for device in self.devices])
        else:
            devices = [device for device in self.devices if device not in device_uids]
            self._logger.debug(f"Device {devices} removed")
            del self.devices[devices[0]]
        self.updater.devices = self.devices

    def is_online(self, uid: str) -> bool:
        """
        Get the online state of a device.

        :param uid: Device UID, something like hdm:ZWave:CBC56091/24
        :return: False, if device is offline, else True
        """
        return False if self.devices.get(uid).status == 1 else True

    def update(self, message: dict):
        """
        Initialize steps needed to update properties on a new message.

        :param message: Message because of which we need to update properties
        """
        self.updater.update(message)


    def _binary_switch(self, uid_info: dict):
        """ Process BinarySwitch properties. """
        if not hasattr(self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))], "binary_switch_property"):
            self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].binary_switch_property = {}
        self._logger.debug(f"Adding binary switch property to {get_device_uid_from_element_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].binary_switch_property[uid_info.get("UID")] = \
            BinarySwitchProperty(uid_info.get("UID"), state=True if uid_info.get("properties").get("state") == 1 else False)
        self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))]. \
            binary_switch_property[uid_info.get("UID")].is_online = self.is_online

    def _general_device(self, uid_info: dict):
        """ Process general device setting (gds) properties. """
        self._logger.debug(f"Adding general device settings to {get_device_uid_from_setting_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_setting_uid(uid_info.get('UID'))]. \
            settings_property["general_device_settings"] = \
            SettingsProperty(element_uid=uid_info.get("UID"),
                             events_enabled=uid_info.get("properties").get("settings").get("eventsEnabled"),
                             name=uid_info.get("properties").get("settings").get("name"),
                             zone_id=uid_info.get("properties").get("settings").get("zoneID"),
                             icon=uid_info.get("properties").get("settings").get("icon"))

    def _inspect_devices(self, devices: list):
        """ Inspect device properties of given list of devices. """
        devices_properties = self.mprm.get_data_from_uid_list(devices)
        for device_properties in devices_properties:
            properties = device_properties.get("properties")
            self.devices[device_properties.get("UID")] = Zwave(**properties)
            self.devices[device_properties.get("UID")].settings_property = {}
            threading.Thread(target=self.devices[device_properties.get("UID")].get_zwave_info).start()

        elements = {"devolo.BinarySwitch": self._binary_switch,
                    "devolo.Meter": self._meter,
                    "devolo.VoltageMultiLevelSensor": self._voltage_multi_level_sensor,
                    "lis.hdm": self._led,
                    "gds.hdm": self._general_device,
                    "cps.hdm": self._parameter,
                    "ps.hdm": self._protection
                    }
        # List comprehension gets the list of uids from every device
        nested_uids_lists = [(uid.get("properties").get('settingUIDs')
                              + uid.get("properties").get("elementUIDs"))
                             for uid in devices_properties]

        # List comprehension gets all uids into one list to make one big call against the mPRM
        uid_list = [uid for sublist in nested_uids_lists for uid in sublist]

        for uid_info in self.mprm.get_data_from_uid_list(uid_list):
            if uid_info.get("UID") is not None:
                elements.get(get_device_type_from_element_uid(uid_info.get("UID")), self._unknown)(uid_info)

    def _led(self, uid_info: dict):
        """ Process LED information setting (lis) properties. """
        self._logger.debug(f"Adding led settings to {get_device_uid_from_setting_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_setting_uid(uid_info.get('UID'))].settings_property["led"] = \
            SettingsProperty(element_uid=uid_info.get("UID"), led_setting=uid_info.get("properties").get("led"))

    def _meter(self, uid_info: dict):
        """ Process Meter properties. """
        if not hasattr(self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))], "consumption_property"):
            self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].consumption_property = {}
        self._logger.debug(f"Adding consumption property to {get_device_uid_from_element_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].consumption_property[uid_info.get("UID")] = \
            ConsumptionProperty(uid_info.get("UID"),
                                current=uid_info.get("properties").get("currentValue"),
                                total=uid_info.get("properties").get("totalValue"),
                                total_since=uid_info.get("properties").get("sinceTime"))

    def _parameter(self, uid_info: dict):
        """ Process custom parameter setting (cps) properties."""
        self._logger.debug(f"Adding parameter settings to {get_device_uid_from_setting_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_setting_uid(uid_info.get('UID'))].settings_property["param_changed"] = \
            SettingsProperty(element_uid=uid_info.get('UID'),
                             param_changed=uid_info.get('properties').get("paramChanged"))

    def _protection(self, uid_info: dict):
        """ Process protection setting (ps) properties. """
        self._logger.debug(f"Adding protection settings to {get_device_uid_from_setting_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_setting_uid(uid_info.get('UID'))].settings_property["protection"] = \
            SettingsProperty(element_uid=uid_info.get('UID'),
                             local_switching=uid_info.get("properties").get("localSwitch"),
                             remote_switching=uid_info.get("properties").get("remoteSwitch"))

    def _unknown(self, uid_info: dict):
        """ Ignore unknown properties. """
        self._logger.debug(f"Found an unexpected element uid: {uid_info.get('UID')}")

    def _voltage_multi_level_sensor(self, uid_info: dict):
        """ Process VoltageMultiLevelSensor properties. """
        if not hasattr(self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))], "voltage_property"):
            self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].voltage_property = {}
        self._logger.debug(f"Adding voltage property to {get_device_uid_from_element_uid(uid_info.get('UID'))}.")
        self.devices[get_device_uid_from_element_uid(uid_info.get("UID"))].voltage_property[uid_info.get("UID")] = \
            VoltageProperty(uid_info.get("UID"), current=uid_info.get("properties").get("value"))


def get_sub_device_uid_from_element_uid(element_uid: str) -> Optional[int]:
    """
    Return the sub device uid of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])
