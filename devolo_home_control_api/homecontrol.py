import logging
import requests
import threading

from .backend.mprm_websocket import MprmWebsocket
from .publisher.publisher import Publisher
from .mydevolo import Mydevolo
from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.settings_property import SettingsProperty
from .properties.voltage_property import VoltageProperty

from devolo_home_control_api.publisher.updater import Updater


class HomeControl:
    def __init__(self, gateway_id, url="https://homecontrol.mydevolo.com"):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url

        mydevolo = Mydevolo.get_instance()

        self.mprm = MprmWebsocket(gateway_id=gateway_id, url=self._mprm_url)
        self.mprm.on_update = self.update
        self.local_ip = self.mprm.detect_gateway_in_lan()

        if self.local_ip:
            self._gateway.local_connection = True
            self.mprm.get_local_session(ip=self.local_ip)
        elif self._gateway.external_access and not mydevolo.maintenance:
            self.mprm.get_remote_session()
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is not possible.")
            raise ConnectionError("Cannot connect to gateway.")

        # Create the initial device dict
        self.devices = {}
        self._inspect_devices()
        self.device_names = dict(zip([self.devices.get(device).name for device in self.devices],
                                     [self.devices.get(device).device_uid for device in self.devices]))


        self.create_pub()
        self.updater = Updater(devices=self.devices, publisher=self.mprm.publisher)

        threading.Thread(target=self.mprm.websocket_connection).start()
        print()

    @property
    def binary_switch_devices(self):
        """Returns all binary switch devices."""
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid),
                                                                         "binary_switch_property")]

    def update(self, message):
        self.updater.update(message)

    def create_pub(self):
        """
        # TODO: Correct docstring
        Create a publisher for every element we support at the moment.
        Actually, there are publisher for current consumption and binary state. Current consumption publisher is create as
        "current_consumption_ELEMENT_UID" and binary state publisher is created as "binary_state_ELEMENT_UID".
        """
        publisher_list = [device for device in self.devices]
        self.mprm.publisher = Publisher(publisher_list)

    def _inspect_devices(self):
        """ Create the initial internal device dict. """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self.mprm.post(data)
        all_devices_list = response.get("result").get("items")[0].get("properties").get("deviceUIDs")
        for device in all_devices_list:
            name, zone, battery_level, icon, element_uids, setting_uids, deviceModelUID, online_state = \
                self.mprm.get_name_and_element_uids(uid=device)
            self._logger.debug(f"Adding {name} ({device}) to device list.")
            # Process device uids
            self.devices[device] = Zwave(name=name,
                                         device_uid=device,
                                         zone=zone,
                                         battery_level=battery_level,
                                         icon=icon,
                                         online_state=online_state)
            self._process_element_uids(device=device, element_uids=element_uids)
            self._process_settings_uids(device=device, setting_uids=setting_uids)

    def _process_element_uids(self, device: str, element_uids: list):
        """ Generate properties depending on the element uid """
        def binary_switch(element_uid: str):
            if not hasattr(self.devices[device], "binary_switch_property"):
                self.devices[device].binary_switch_property = {}
            self._logger.debug(f"Adding binary switch property to {device}.")
            self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid)
            self.devices[device].binary_switch_property[element_uid].get_binary_switch_state()

        def meter(element_uid: str):
            if not hasattr(self.devices[device], "consumption_property"):
                self.devices[device].consumption_property = {}
            self._logger.debug(f"Adding consumption property to {device}.")
            self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid)
            self.devices[device].consumption_property[element_uid].get_consumption('current')
            self.devices[device].consumption_property[element_uid].get_consumption('total')

        def voltage_multi_level_sensor(element_uid: str):
            if not hasattr(self.devices[device], "voltage_property"):
                self.devices[device].voltage_property = {}
            self._logger.debug(f"Adding voltage property to {device}.")
            self.devices[device].voltage_property[element_uid] = VoltageProperty(element_uid)
            self.devices[device].voltage_property[element_uid].get_voltage(element_uid)

        device_type = {"devolo.BinarySwitch": binary_switch,
                       "devolo.Meter": meter,
                       "devolo.VoltageMultiLevelSensor": voltage_multi_level_sensor}

        for element_uid in element_uids:
            try:
                device_type[get_device_type_from_element_uid(element_uid)](element_uid)
            except KeyError:
                self._logger.debug(f"Found an unexpected element uid: {element_uid}")

    def _process_settings_uids(self, device, setting_uids):
        """Generate properties depending on the setting uid"""
        def led(setting_uid):
            device = get_device_uid_from_setting_uid(setting_uid)
            self._logger.debug(f"Adding led settings to {device}.")
            self.devices[device].settings_property["led"] = SettingsProperty(element_uid=setting_uid, led_setting=None)
            self.devices[device].settings_property["led"].get_led_setting()

        def general_device(setting_uid):
            device = get_device_uid_from_setting_uid(setting_uid)
            self._logger.debug(f"Adding general device settings to {device}.")
            self.devices[device].settings_property["general_device_settings"] = SettingsProperty(element_uid=setting_uid,
                                                                                                 events_enabled=None,
                                                                                                 name=None,
                                                                                                 zone_id=None,
                                                                                                 icon=None)
            self.devices[device].settings_property["general_device_settings"].get_general_device_settings()

        def parameter(setting_uid):
            device = get_device_uid_from_setting_uid(setting_uid)
            self._logger.debug(f"Adding parameter settings to {device}.")
            self.devices[device].settings_property["param_changed"] = SettingsProperty(element_uid=setting_uid,
                                                                                       param_changed=None)
            self.devices[device].settings_property["param_changed"].get_param_changed_setting()

        def protection(setting_uid):
            device = get_device_uid_from_setting_uid(setting_uid)
            self._logger.debug(f"Adding protection settings to {device}.")
            self.devices[device].settings_property["protection"] = SettingsProperty(element_uid=setting_uid,
                                                                                    local_switching=None,
                                                                                    remote_switching=None)
            self.devices[device].settings_property["protection"].get_protection_setting(protection_setting="local")
            self.devices[device].settings_property["protection"].get_protection_setting(protection_setting="remote")

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


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    return element_uid.split(":", 1)[1].split("#")[0]


def get_device_type_from_element_uid(element_uid: str) -> str:
    """
    Return the device type of the given element uid

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]


def get_device_uid_from_setting_uid(setting_uid: str) -> str:
    """
    Return the device uid of the given setting uid

    :param setting_uid: Setting UID, something like lis.hdm:ZWave:EB5A9F6C/2
    :return: Device UID, something like hdm:ZWave:EB5A9F6C/2
    """
    return setting_uid.split(".", 1)[-1]


def get_sub_device_uid_from_element_uid(element_uid: str) -> int:
    """
    Return the sub device uid of the given element uid

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])