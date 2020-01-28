import json
import logging
import socket
import time

import requests
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.voltage_property import VoltageProperty
from .properties.settings_property import SettingsProperty


class MprmRest:
    """
    The MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    """

    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url

        local_ip = self._detect_gateway_in_lan()

        if local_ip:
            # Get a local session
            self._logger.info("Connecting to gateway locally")
            self._mprm_url = "http://" + local_ip
            self._token_url = self._session.get(self._mprm_url + "/dhlp/portal/full",
                                                auth=(self._gateway.local_user, self._gateway.local_passkey)).json()
            self._session.get(self._token_url.get('link'))
        elif self._gateway.external_access:
            # Get a remote session, if we are allowed to
            self._logger.info("Connecting to gateway via cloud")
            self._session.get(self._gateway.full_url)
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is prohibited.")
            raise ConnectionError("Cannot connect to gateway.")

        # create the initial device dict
        self.devices = {}
        self._inspect_devices()
        # TODO: Why don't we update the devices at start?

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
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise ValueError("Not a valid uid to get binary switch data")
        response = self._extract_data_from_element_uid(element_uid)
        self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.get(element_uid).state = True if response.get("properties").get("state") == 1 else False
        return self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.get(element_uid).state

    def get_consumption(self, element_uid: str, consumption_type: str = "current") -> float:
        """
        Update and return the consumption, specified in consumption_type for the given uid.

        :param element_uid: element UID of the consumption. Usually starts with devolo.Meter
        :param consumption_type: current or total consumption
        :return: Consumption
        """
        if consumption_type not in ["current", "total"]:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        response = self._extract_data_from_element_uid(element_uid)
        if consumption_type == "current":
            self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current = response.get("properties").get("currentValue")
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current
        else:
            self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).total = response.get("properties").get("totalValue")
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).total

    def get_voltage(self, element_uid: str) -> float:
        """
        Update and return the voltage
        :param element_uid: element UID of the voltage. Usually starts with devolo.VoltageMultiLevelSensor
        :return: voltage
        """
        response = self._extract_data_from_element_uid(element_uid)
        self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.get(element_uid).current = response.get("properties").get("value")
        return self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.get(element_uid).current

    def set_binary_switch(self, element_uid, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param element_uid: element_uid as string
        :param state: True if switching on, False if switching off
        """
        # TODO: We should think about how to prevent an jumping binary switch in the UI of hass
        # Maybe set the state of the binary internally without waiting for the websocket to tell us the state.
        data = {"method": "FIM/invokeOperation",
                "params": [element_uid, "turnOn" if state else "turnOff", []]}
        self._post(data)
        # TODO: Catch errors!


    def _detect_gateway_in_lan(self):
        """ Detects a gateway in local network and check if it is the desired one. """
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                zeroconf.get_service_info(service_type, name)

        local_ip = None
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])
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
                    # Got IPv6 address which isn't supported by socket.inet_ntoa
                    self._logger.debug(f"Found an IPv6 address. This cannot be a gateway.")
        zeroconf.close()
        return local_ip

    def _extract_data_from_element_uid(self, element_uid):
        """ Returns data from an element_uid using a RPC call """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[element_uid], 0]}
        response = self._post(data)
        # TODO: Catch error!
        return response.get("result").get("items")[0]

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
               properties.get("deviceModelUID")

    def _inspect_devices(self):
        """ Create the initial internal device dict. """
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self._post(data)
        for item in response.get("result").get("items"):
            all_devices_list = item.get("properties").get("deviceUIDs")
            for device in all_devices_list:
                name, zone, battery_level, icon, element_uids, setting_uids, deviceModelUID = self._get_name_and_element_uids(uid=device)
                self.devices[device] = Zwave(name=name,
                                             device_uid=device,
                                             zone=zone,
                                             battery_level=battery_level,
                                             icon=icon)
                for element_uid in element_uids:
                    if get_device_type_from_element_uid(element_uid) == "devolo.BinarySwitch":
                        if not hasattr(self.devices[device], "binary_switch_property"):
                            self.devices[device].binary_switch_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as binary switch property.")
                        self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid)
                    elif get_device_type_from_element_uid(element_uid) == "devolo.Meter":
                        if not hasattr(self.devices[device], "consumption_property"):
                            self.devices[device].consumption_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as consumption property.")
                        self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid)
                    elif get_device_type_from_element_uid(element_uid) == "devolo.VoltageMultiLevelSensor":
                        if not hasattr(self.devices[device], "voltage_property"):
                            self.devices[device].voltage_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as voltage property.")
                        self.devices[device].voltage_property[element_uid] = VoltageProperty(element_uid)
                    else:
                        self._logger.debug(f"Found an unexpected element uid: {element_uid}")
                for setting_uid in setting_uids:
                    if get_device_type_from_element_uid(setting_uid) == "lis.hdm":
                        if not hasattr(self.devices[device], "settings_property"):
                            self.devices[device].settings_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as settings property")
                        self.devices[device].settings_property[setting_uid] = SettingsProperty(element_uid=setting_uid,
                                                                                               led_setting=None)

    def _post(self, data: dict) -> dict:
        """ Communicate with the RPC interface. """
        self._data_id += 1
        data['jsonrpc'] = "2.0"
        data['id'] = self._data_id
        response = self._session.post(self._mprm_url + "/remote/json-rpc",
                                      data=json.dumps(data),
                                      headers={"content-type": "application/json"}).json()
        # TODO: Catch errors!
        if response['id'] != self._data_id:
            self._logger.error("Got an unexpected response after posting data.")
            raise ValueError("Got an unexpected response after posting data.")
        return response


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: device UID, something like hdm:ZWave:CBC56091/24
    """
    return element_uid.split(":", 1)[1].split("#")[0]


def get_device_type_from_element_uid(element_uid):
    """
    Return the device type of the given element uid

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]
