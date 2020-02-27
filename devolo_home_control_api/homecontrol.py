import logging
import threading
from typing import Optional

import requests

from .backend.mprm_websocket import MprmWebsocket
from .devices.gateway import Gateway
from .devices.zwave import Zwave, get_device_type_from_element_uid
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
        self._inspect_devices()
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
    def publisher(self) -> Publisher:
        """ Get all publisher. """
        return self.mprm.publisher


    def create_pub(self):
        """ Create a publisher for every device. """
        self.mprm.publisher = Publisher([device for device in self.devices])

    def device_change(self, uids: list):
        """
        React on new devices or removed devices. As the Z-Wave controller can only be in inclusion or exclusion mode, we
        assume, that you cannot add and remove devices at the same time. So if the number of devices increases, there is
        a new one and if the number decreases, a device was removed.

        :param uids: List of UIDs known by the backend
        """
        if len(uids) > len(self.devices):
            new_device = [device for device in uids if device not in self.devices]
            self._logger.debug(f"New device found {new_device}")
            self._inspect_device(new_device[0])
            self.mprm.publisher = Publisher([device for device in self.devices])
        else:
            devices = [device for device in self.devices if device not in uids]
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


    def _binary_switch(self, device: str, element_uid: str):
        if not hasattr(self.devices[device], "binary_switch_property"):
            self.devices[device].binary_switch_property = {}
        self._logger.debug(f"Adding binary switch property to {device}.")
        self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid)
        self.devices[device].binary_switch_property[element_uid].is_online = self.is_online
        self.devices[device].binary_switch_property[element_uid].fetch_binary_switch_state()

    def _general_device(self, device: str, setting_uid: str):
        self._logger.debug(f"Adding general device settings to {device}.")
        self.devices[device].settings_property["general_device_settings"] = SettingsProperty(element_uid=setting_uid,
                                                                                             events_enabled=None,
                                                                                             name=None,
                                                                                             zone_id=None,
                                                                                             icon=None)
        self.devices[device].settings_property["general_device_settings"].fetch_general_device_settings()

    def _inspect_devices(self):
        for device in self.mprm.get_all_devices():
            self._inspect_device(device)

    def _inspect_device(self, device: str):
        properties = self.mprm.get_name_and_element_uids(uid=device)
        self.devices[device] = Zwave(**properties)
        self.devices[device].settings_property = {}

        elements = {"devolo.BinarySwitch": self._binary_switch,
                    "devolo.Meter": self._meter,
                    "devolo.VoltageMultiLevelSensor": self._voltage_multi_level_sensor,
                    "lis.hdm": self._led,
                    "gds.hdm": self._general_device,
                    "cps.hdm": self._parameter,
                    "ps.hdm": self._protection
                    }

        for element_uid in properties.get("elementUIDs") + properties.get("settingUIDs"):
            if element_uid is not None:
                elements.get(get_device_type_from_element_uid(element_uid), self._unknown)(device, element_uid)

    def _led(self, device: str, setting_uid: str):
        self._logger.debug(f"Adding led settings to {device}.")
        self.devices[device].settings_property["led"] = SettingsProperty(element_uid=setting_uid, led_setting=None)
        self.devices[device].settings_property["led"].fetch_led_setting()

    def _meter(self, device: str, element_uid: str):
        if not hasattr(self.devices[device], "consumption_property"):
            self.devices[device].consumption_property = {}
        self._logger.debug(f"Adding consumption property to {device}.")
        self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid)
        self.devices[device].consumption_property[element_uid].fetch_consumption('current')
        self.devices[device].consumption_property[element_uid].fetch_consumption('total')

    def _parameter(self, device: str, setting_uid: str):
        self._logger.debug(f"Adding parameter settings to {device}.")
        self.devices[device].settings_property["param_changed"] = SettingsProperty(element_uid=setting_uid,
                                                                                   param_changed=None)
        self.devices[device].settings_property["param_changed"].fetch_param_changed_setting()

    def _protection(self, device: str, setting_uid: str):
        self._logger.debug(f"Adding protection settings to {device}.")
        self.devices[device].settings_property["protection"] = SettingsProperty(element_uid=setting_uid,
                                                                                local_switching=None,
                                                                                remote_switching=None)
        self.devices[device].settings_property["protection"].fetch_protection_setting(protection_setting="local")
        self.devices[device].settings_property["protection"].fetch_protection_setting(protection_setting="remote")

    def _unknown(self, device: str, element_uid: str):
        self._logger.debug(f"Found an unexpected element uid: {element_uid} at device {device}")

    def _voltage_multi_level_sensor(self, device: str, element_uid: str):
        if not hasattr(self.devices[device], "voltage_property"):
            self.devices[device].voltage_property = {}
        self._logger.debug(f"Adding voltage property to {device}.")
        self.devices[device].voltage_property[element_uid] = VoltageProperty(element_uid)
        self.devices[device].voltage_property[element_uid].fetch_voltage()


def get_sub_device_uid_from_element_uid(element_uid: str) -> Optional[int]:
    """
    Return the sub device uid of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])
