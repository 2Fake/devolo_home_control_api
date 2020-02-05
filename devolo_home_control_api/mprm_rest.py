import json
import logging
import socket
import time

import requests
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .mydevolo import Mydevolo
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.settings_property import SettingsProperty
from .properties.voltage_property import VoltageProperty


class MprmRest:
    """
    The MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    :raises: JSONDecodeError: Connecting to the gateway was not possible
    """

    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url

        mydevolo = Mydevolo.get_instance()
        self.local_ip = self._detect_gateway_in_lan()

        if self.local_ip:
            self._gateway.local_connection = True
            self._get_local_session()
        elif self._gateway.external_access and not mydevolo.maintenance:
            self._get_remote_session()
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is not possible.")
            raise ConnectionError("Cannot connect to gateway.")

        # create the initial device dict
        self.devices = {}
        self._inspect_devices()

    @property
    def binary_switch_devices(self):
        """Returns all binary switch devices."""
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid),
                                                                         "binary_switch_property")]


    def get_binary_switch_state(self, element_uid: str) -> bool:
        """
        Update and return the binary switch state for the given uid.

        :param element_uid: element UID of the consumption. Usually starts with devolo.BinarySwitch
        :return: Binary switch state
        """
        if not element_uid.startswith("devolo.BinarySwitch"):
            raise ValueError("Not a valid uid to get binary switch data.")
        response = self._extract_data_from_element_uid(element_uid)
        self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.get(element_uid).state = \
            True if response.get("properties").get("state") == 1 else False
        return self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.get(element_uid).state

    def get_consumption(self, element_uid: str, consumption_type: str = "current") -> float:
        """
        Update and return the consumption, specified in consumption_type for the given uid.

        :param element_uid: Element UID of the consumption. Usually starts with devolo.Meter.
        :param consumption_type: Current or total consumption
        :return: Consumption
        """
        if not element_uid.startswith("devolo.Meter"):
            raise ValueError("Not a valid uid to get consumption data.")
        if consumption_type not in ["current", "total"]:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        response = self._extract_data_from_element_uid(element_uid)
        if consumption_type == "current":
            self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current = \
                response.get("properties").get("currentValue")
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current
        else:
            self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).total = \
                response.get("properties").get("totalValue")
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).total

    def get_device_uid_from_name(self, name: str, zone: str = "") -> str:
        """
        Get device from name. Sometimes, the name is ambiguous. Then hopefully the zone makes it unique.

        :param name: Name of the device
        :param zone: Zone the device is in. Only needed, if device name is ambiguous.
        :return: Device UID
        """
        device_list = []
        for device in self.devices.values():
            if device.name == name:
                device_list.append(device)
        if len(device_list) == 0:
            raise MprmDeviceNotFoundError(f'There is no device "{name}"')
        elif len(device_list) > 1 and zone == "":
            raise MprmDeviceNotFoundError(f'The name "{name}" is ambiguous ({len(device_list)} times). Please provide a zone.')
        elif len(device_list) > 1:
            for device in device_list:
                if device.zone == zone:
                    return device.device_uid
            else:
                raise MprmDeviceNotFoundError(f'There is no device "{name}" in zone "{zone}".')
        else:
            return device_list[0].device_uid

    def get_led_setting(self, setting_uid: str) -> bool:
        """
        Update and return the led setting.

        :param setting_uid: Setting UID of the LED setting. Usually starts with lis.hdm.
        :return: LED setting
        """
        if not setting_uid.startswith("lis.hdm"):
            raise ValueError("Not a valid uid to get the led setting")
        response = self._extract_data_from_element_uid(setting_uid)
        self.devices.get(get_device_uid_from_setting_uid(setting_uid)).settings_property.get("led").led_setting = \
            response.get("properties").get("led")
        return self.devices.get(get_device_uid_from_setting_uid(setting_uid)).settings_property.get("led").led_setting

    def get_general_device_settings(self, setting_uid: str) -> bool:
        """
        Update and return the events enabled setting. If a device shall report to the diary, this is true.

        :param setting_uid: Settings UID to look at. Usually starts with gds.hdm.
        :return: Events enabled or not
        """
        if not setting_uid.startswith("gds.hdm"):
            raise ValueError("Not a valid uid to get the events enabled setting.")
        response = self._extract_data_from_element_uid(setting_uid)
        gds = self.devices.get(get_device_uid_from_setting_uid(setting_uid)).settings_property.get("general_device_settings")
        gds.name = response.get("properties").get("name")
        gds.icon = response.get("properties").get("icon")
        gds.zone_id = response.get("properties").get("zoneID")
        gds.events_enabled = response.get("properties").get("eventsEnabled")
        return gds.name, gds.icon, gds.zone_id, gds.events_enabled

    def get_param_changed_setting(self, setting_uid: str) -> bool:
        """
        Update and return the param changed setting. If a device has modified Z-Wave parameters, this is true.

        :param setting_uid: Settings UID to look at. Usually starts with cps.hdm.
        :return: Parameter changed or not
        """
        if not setting_uid.startswith("cps.hdm"):
            raise ValueError("Not a valid uid to get the param changed setting")
        response = self._extract_data_from_element_uid(setting_uid)
        device_uid = get_device_uid_from_setting_uid(setting_uid)
        self.devices.get(device_uid).settings_property.get("param_changed").param_changed = \
            response.get("properties").get("paramChanged")
        return self.devices.get(device_uid).settings_property.get("param_changed").param_changed

    def get_protection_setting(self, setting_uid, protection_setting):
        """
        Update and return the protection setting. There are only two protection settings. Local and remote switching.

        :param setting_uid: Settings UID to look at. Usually starts with ps.hdm.
        :param protection_setting: Look at local or remote switching.
        :return: Switching is protected or not
        """
        if not setting_uid.startswith("ps.hdm"):
            raise ValueError("Not a valid uid to get the protection setting")
        if protection_setting not in ["local", "remote"]:
            raise ValueError("Only local and remote are possible protection settings")
        response = self._extract_data_from_element_uid(setting_uid)
        setting_property = self.devices.get(get_device_uid_from_setting_uid(setting_uid)).settings_property.get("led")
        if protection_setting == "local":
            setting_property.local_switching = response.get("properties").get("localSwitch")
            return setting_property.local_switching
        else:
            setting_property.remote_switching = response.get("properties").get("remoteSwitch")
            return setting_property.remote_switching

    def get_voltage(self, element_uid: str) -> float:
        """
        Update and return the voltage

        :param element_uid: Element UID of the voltage. Usually starts with devolo.VoltageMultiLevelSensor
        :return: Voltage value
        """
        if not element_uid.startswith("devolo.VoltageMultiLevelSensor"):
            raise ValueError("Not a valid uid to get consumption data.")
        response = self._extract_data_from_element_uid(element_uid)
        self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.get(element_uid).current = \
            response.get("properties").get("value")
        return self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.get(element_uid).current

    def set_binary_switch(self, element_uid: str, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param element_uid: element_uid
        :param state: True if switching on, False if switching off
        """
        if not element_uid.startswith("devolo.BinarySwitch"):
            raise ValueError("Not a valid uid to set binary switch data.")
        if type(state) != bool:
            raise ValueError("Not a valid binary switch state.")
        data = {"method": "FIM/invokeOperation",
                "params": [element_uid, "turnOn" if state else "turnOff", []]}
        device_uid = get_device_uid_from_element_uid(element_uid)
        response = self._post(data)
        if response.get("result").get("status") == 1:
            self.devices.get(device_uid).binary_switch_property.get(element_uid).state = state
        elif response.get("result").get("status") == 2 \
                and not self._device_usable(get_device_uid_from_element_uid(element_uid)):
            raise MprmDeviceCommunicationError("The device is offline.")
        else:
            self._logger.info(f"Could not set state of device {device_uid}. Maybe it is already at this state.")
            self._logger.info(f"Target state is {state}.")
            self._logger.info(f"Actual state is {self.devices.get(device_uid).binary_switch_property.get(element_uid).state}.")


    def _detect_gateway_in_lan(self):
        """ Detects a gateway in local network and check if it is the desired one. """
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                zeroconf.get_service_info(service_type, name)

        local_ip = None
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])
        self._logger.info("Searching for gateway in LAN")
        # TODO: Optimize the sleep
        time.sleep(2)
        for mdns_name in zeroconf.cache.entries():
            if hasattr(mdns_name, "address"):
                try:
                    ip = socket.inet_ntoa(mdns_name.address)
                    if requests.get("http://" + ip + "/dhlp/port/full",
                                    auth=(self._gateway.local_user, self._gateway.local_passkey),
                                    timeout=0.5).status_code == requests.codes.ok:
                        self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                        local_ip = ip
                        break
                except OSError:
                    # Got IPv6 address which isn't supported by socket.inet_ntoa and the gateway as well.
                    self._logger.debug(f"Found an IPv6 address. This cannot be a gateway.")
        zeroconf.close()
        return local_ip

    def _device_usable(self, uid):
        """
        Return the 'online' state of the given device as bool.
        We consider everything as 'online' if the device can receive new values.
        """
        return True if self.devices.get(uid).online in ["online"] else False

    def _extract_data_from_element_uid(self, element_uid):
        """ Returns data from an element_uid using a RPC call """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[element_uid], 0]}
        response = self._post(data)
        # TODO: Catch error!
        return response.get("result").get("items")[0]

    def _get_local_session(self):
        """ Connect to the gateway locally. """
        self._logger.info("Connecting to gateway locally")
        self._mprm_url = "http://" + self.local_ip
        try:
            self._token_url = self._session.get(self._mprm_url + "/dhlp/portal/full",
                                                auth=(self._gateway.local_user, self._gateway.local_passkey), timeout=5).json()
        except json.JSONDecodeError:
            self._logger.error("Could not connect to the gateway locally.")
            raise MprmDeviceCommunicationError("Could not connect to the gateway locally.") from None
        except requests.ConnectTimeout:
            self._logger.error("Timeout during connecting to the gateway.")
            raise
        self._session.get(self._token_url.get('link'))

    def _get_name_and_element_uids(self, uid):
        """ Returns the name, all element UIDs and the device model of the given device UID. """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self._post(data)
        properties = response.get("result").get("items")[0].get("properties")
        return properties.get("itemName"),\
            properties.get("zone"),\
            properties.get("batteryLevel"),\
            properties.get("icon"),\
            properties.get("elementUIDs"),\
            properties.get("settingUIDs"),\
            properties.get("deviceModelUID"),\
            properties.get("status")

    def _get_remote_session(self):
        """ Connect to the gateway remotely. """
        self._logger.info("Connecting to gateway via cloud")
        try:
            self._session.get(self._gateway.full_url)
        except json.JSONDecodeError:
            raise MprmDeviceCommunicationError("Gateway is offline.") from None

    def _inspect_devices(self):
        """ Create the initial internal device dict. """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self._post(data)
        all_devices_list = response.get("result").get("items")[0].get("properties").get("deviceUIDs")
        for device in all_devices_list:
            name, zone, battery_level, icon, element_uids, setting_uids, deviceModelUID, online_state = \
                self._get_name_and_element_uids(uid=device)
            # Process device uids
            self.devices[device] = Zwave(name=name,
                                         device_uid=device,
                                         zone=zone,
                                         battery_level=battery_level,
                                         icon=icon,
                                         online_state=online_state)
            self._process_element_uids(device=device, name=name, element_uids=element_uids)
            self._process_settings_uids(device=device, name=name, setting_uids=setting_uids)

    def _post(self, data: dict) -> dict:
        """ Communicate with the RPC interface. """
        if not(self._gateway.online or self._gateway.sync) and not self._gateway.local_connection:
            raise MprmDeviceCommunicationError("Gateway is offline.")

        self._data_id += 1
        data['jsonrpc'] = "2.0"
        data['id'] = self._data_id
        try:
            response = self._session.post(self._mprm_url + "/remote/json-rpc",
                                          data=json.dumps(data),
                                          headers={"content-type": "application/json"},
                                          timeout=15).json()
        except requests.ReadTimeout:
            self._logger.error("Gateway is offline.")
            self._gateway.update_state(False)
            raise MprmDeviceCommunicationError("Gateway is offline.") from None
        if response['id'] != data['id']:
            self._logger.error("Got an unexpected response after posting data.")
            raise ValueError("Got an unexpected response after posting data.")
        return response

    def _process_element_uids(self, device, name, element_uids):
        """ Generate properties depending on the element uid """
        for element_uid in element_uids:
            if get_device_type_from_element_uid(element_uid) == "devolo.BinarySwitch":
                if not hasattr(self.devices[device], "binary_switch_property"):
                    self.devices[device].binary_switch_property = {}
                self._logger.debug(f"Adding {name} ({device}) to device list as binary switch property.")
                self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid)
                self.get_binary_switch_state(element_uid)
            elif get_device_type_from_element_uid(element_uid) == "devolo.Meter":
                if not hasattr(self.devices[device], "consumption_property"):
                    self.devices[device].consumption_property = {}
                self._logger.debug(f"Adding {name} ({device}) to device list as consumption property.")
                self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid)
                for consumption in ['current', 'total']:
                    self.get_consumption(element_uid, consumption)
            elif get_device_type_from_element_uid(element_uid) == "devolo.VoltageMultiLevelSensor":
                if not hasattr(self.devices[device], "voltage_property"):
                    self.devices[device].voltage_property = {}
                self._logger.debug(f"Adding {name} ({device}) to device list as voltage property.")
                self.devices[device].voltage_property[element_uid] = VoltageProperty(element_uid)
                self.get_voltage(element_uid)
            else:
                self._logger.debug(f"Found an unexpected element uid: {element_uid}")

    def _process_settings_uids(self, device, name, setting_uids):
        """Generate properties depending on the setting uid"""
        for setting_uid in setting_uids:
            if not hasattr(self.devices[device], "settings_property"):
                self.devices[device].settings_property = {}
            if get_device_type_from_element_uid(setting_uid) == "lis.hdm":
                self._logger.debug(f"Adding {name} ({device}) to device list as settings property")
                self.devices[device].settings_property["led"] = SettingsProperty(element_uid=setting_uid,
                                                                                 led_setting=None)
                self.get_led_setting(setting_uid)
            elif get_device_type_from_element_uid(setting_uid) == "gds.hdm":
                self.devices[device].settings_property["general_device_settings"] = SettingsProperty(element_uid=setting_uid,
                                                                                                     events_enabled=None,
                                                                                                     name=None,
                                                                                                     zone_id=None,
                                                                                                     icon=None)
                self.get_general_device_settings(setting_uid)
            elif get_device_type_from_element_uid(setting_uid) == "cps.hdm":
                self.devices[device].settings_property["param_changed"] = SettingsProperty(element_uid=setting_uid,
                                                                                           param_changed=None)
                self.get_param_changed_setting(setting_uid)
            elif get_device_type_from_element_uid(setting_uid) == "ps.hdm":
                self.devices[device].settings_property["protection"] = SettingsProperty(element_uid=setting_uid,
                                                                                        local_switching=None,
                                                                                        remote_switching=None)
                for protection in ["local", "remote"]:
                    # TODO: find a better way for this loop.
                    self.get_protection_setting(setting_uid=setting_uid, protection_setting=protection)
            else:
                self._logger.debug(f"Found an unexpected element uid: {setting_uid}")


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    return element_uid.split(":", 1)[1].split("#")[0]


def get_device_type_from_element_uid(element_uid):
    """
    Return the device type of the given element uid

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]


def get_device_uid_from_setting_uid(setting_uid):
    """
    Return the device uid of the given setting uid
    :param setting_uid: Setting UID, something like lis.hdm:ZWave:EB5A9F6C/2
    :return: Device UID, something like hdm:ZWave:EB5A9F6C/2
    """
    return setting_uid.split(".", 1)[-1]


class MprmDeviceCommunicationError(Exception):
    """ Communicating to a device via mPRM failed """


class MprmDeviceNotFoundError(Exception):
    """ A device like this was not found """
