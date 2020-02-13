import json
import logging
import socket
import time

import requests
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from ..devices.gateway import Gateway


class MprmRest:
    """
    The MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM (typically leave it at default)
    :raises: JSONDecodeError: Connecting to the gateway was not possible
    """

    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            raise SyntaxError(f"Please init {cls.__name__}() once to establish a connection to the gateway's backend.")
        return cls.__instance

    @classmethod
    def del_instance(cls):
        cls.__instance = None


    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        if self.__class__.__instance is not None:
            raise SyntaxError(f"Please use {self.__class__.__name__}.get_instance() to reuse the connection to the backend.")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url
        self._local_ip = None

        self.__class__.__instance = self


    def detect_gateway_in_lan(self):
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
            try:
                ip = socket.inet_ntoa(mdns_name.address)
                if mdns_name.key.startswith("devolo-homecontrol") and \
                        requests.get("http://" + ip + "/dhlp/port/full",
                                     auth=(self._gateway.local_user, self._gateway.local_passkey),
                                     timeout=0.5).status_code == requests.codes.ok:
                    self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                    self._local_ip = ip
                    break
            except OSError:
                # Got IPv6 address which isn't supported by socket.inet_ntoa and the gateway as well.
                self._logger.debug(f"Found an IPv6 address. This cannot be a gateway.")
            except AttributeError:
                # The MDNS entry does not provide address information
                pass
        else:
            self._logger.debug("Could not find a gateway in local LAN with provided user and password.")
        zeroconf.close()
        return self._local_ip

    def create_connection(self):
        if self._local_ip:
            self._gateway.local_connection = True
            self.get_local_session()
        elif self._gateway.external_access:
            # TODO: get maintenance check back
            # elif self._gateway.external_access and not mydevolo.maintenance:
            self.get_remote_session()
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is not possible.")
            raise ConnectionError("Cannot connect to gateway.")

    def _device_usable(self, uid):
        """
        Return the 'online' state of the given device as bool.
        We consider everything as 'online' if the device can receive new values.
        """
        return True if self.devices.get(uid).online in ["online"] else False

    def extract_data_from_element_uid(self, element_uid):
        """ Returns data from an element_uid using a RPC call """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[element_uid], 0]}
        response = self.post(data)
        # TODO: Catch error!
        return response.get("result").get("items")[0]

    def get_local_session(self):
        """ Connect to the gateway locally. """
        self._logger.info("Connecting to gateway locally")
        self._mprm_url = "http://" + self._local_ip
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

    def get_name_and_element_uids(self, uid):
        """ Returns the name, all element UIDs and the device model of the given device UID. """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self.post(data)
        properties = response.get("result").get("items")[0].get("properties")
        return properties.get("itemName"),\
            properties.get("zone"),\
            properties.get("batteryLevel"),\
            properties.get("icon"),\
            properties.get("elementUIDs"),\
            properties.get("settingUIDs"),\
            properties.get("deviceModelUID"),\
            properties.get("status")

    def get_remote_session(self):
        """ Connect to the gateway remotely. """
        self._logger.info("Connecting to gateway via cloud")
        try:
            self._session.get(self._gateway.full_url)
        except json.JSONDecodeError:
            raise MprmDeviceCommunicationError("Gateway is offline.") from None

    def post(self, data: dict) -> dict:
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


class MprmDeviceCommunicationError(Exception):
    """ Communicating to a device via mPRM failed """


class MprmDeviceNotFoundError(Exception):
    """ A device like this was not found """
