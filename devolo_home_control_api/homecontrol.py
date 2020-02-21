import logging
import threading

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
        publisher_list = [device for device in self.devices]
        self.mprm.publisher = Publisher(publisher_list)

    def is_online(self, uid: str) -> bool:
        """
        Get the online state of a device.

        :param uid: Device UID, something like hdm:ZWave:CBC56091/24
        :return: True, if device is online
        """
        return False if self.devices.get(uid).status == 1 else True

    def update(self, message: str):
        """ Initialize steps needed to update properties on a new message. """
        self.updater.update(message)


    def _inspect_devices(self):
        """ Create the initial internal device dict. """
        for device in self.mprm.get_all_devices():
            properties = dict([(key, value) for key, value in self.mprm.get_name_and_element_uids(uid=device).items()])
            self.devices[device] = Zwave(**properties)
            self._process_element_uids(device=device, element_uids=properties.get("elementUIDs"))
            self._process_settings_uids(device=device, setting_uids=properties.get("settingUIDs"))

    def _process_element_uids(self, device: str, element_uids: list):
        """ Generate properties depending on the element uid. """
        def binary_switch(element_uid: str):
            if not hasattr(self.devices[device], "binary_switch_property"):
                self.devices[device].binary_switch_property = {}
            self._logger.debug(f"Adding binary switch property to {device}.")
            self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid)
            self.devices[device].binary_switch_property[element_uid].is_online = self.is_online
            self.devices[device].binary_switch_property[element_uid].fetch_binary_switch_state()

        def meter(element_uid: str):
            if not hasattr(self.devices[device], "consumption_property"):
                self.devices[device].consumption_property = {}
            self._logger.debug(f"Adding consumption property to {device}.")
            self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid)
            self.devices[device].consumption_property[element_uid].fetch_consumption('current')
            self.devices[device].consumption_property[element_uid].fetch_consumption('total')

        def voltage_multi_level_sensor(element_uid: str):
            if not hasattr(self.devices[device], "voltage_property"):
                self.devices[device].voltage_property = {}
            self._logger.debug(f"Adding voltage property to {device}.")
            self.devices[device].voltage_property[element_uid] = VoltageProperty(element_uid)
            self.devices[device].voltage_property[element_uid].fetch_voltage()

        device_type = {"devolo.BinarySwitch": binary_switch,
                       "devolo.Meter": meter,
                       "devolo.VoltageMultiLevelSensor": voltage_multi_level_sensor}

        for element_uid in element_uids:
            try:
                device_type[get_device_type_from_element_uid(element_uid)](element_uid)
            except KeyError:
                self._logger.debug(f"Found an unexpected element uid: {element_uid}")

    def _process_settings_uids(self, device: str, setting_uids: list):
        """ Generate properties depending on the setting uid. """
        def led(setting_uid: str):
            self._logger.debug(f"Adding led settings to {device}.")
            self.devices[device].settings_property["led"] = SettingsProperty(element_uid=setting_uid, led_setting=None)
            self.devices[device].settings_property["led"].fetch_led_setting()

        def general_device(setting_uid: str):
            self._logger.debug(f"Adding general device settings to {device}.")
            self.devices[device].settings_property["general_device_settings"] = SettingsProperty(element_uid=setting_uid,
                                                                                                 events_enabled=None,
                                                                                                 name=None,
                                                                                                 zone_id=None,
                                                                                                 icon=None)
            self.devices[device].settings_property["general_device_settings"].fetch_general_device_settings()

        def parameter(setting_uid: str):
            self._logger.debug(f"Adding parameter settings to {device}.")
            self.devices[device].settings_property["param_changed"] = SettingsProperty(element_uid=setting_uid,
                                                                                       param_changed=None)
            self.devices[device].settings_property["param_changed"].fetch_param_changed_setting()

        def protection(setting_uid: str):
            self._logger.debug(f"Adding protection settings to {device}.")
            self.devices[device].settings_property["protection"] = SettingsProperty(element_uid=setting_uid,
                                                                                    local_switching=None,
                                                                                    remote_switching=None)
            self.devices[device].settings_property["protection"].fetch_protection_setting(protection_setting="local")
            self.devices[device].settings_property["protection"].fetch_protection_setting(protection_setting="remote")

        if not hasattr(self.devices[device], "settings_property"):
            self.devices[device].settings_property = {}

        setting = {"lis.hdm": led,
                   "gds.hdm": general_device,
                   "cps.hdm": parameter,
                   "ps.hdm": protection}

        for setting_uid in setting_uids:
            try:
                setting[get_device_type_from_element_uid(setting_uid)](setting_uid)
            except KeyError:
                self._logger.debug(f"Found an unexpected element uid: {setting_uid}")


def get_sub_device_uid_from_element_uid(element_uid: str) -> int:
    """
    Return the sub device uid of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])
