import json
import logging
import socket
import threading
import time

import requests
from zeroconf import DNSRecord, ServiceBrowser, ServiceStateChange, Zeroconf

from ..devices.gateway import Gateway
from ..mydevolo import Mydevolo


class MprmRest:
    """
    The MprmRest object handles calls to the so called mPRM as singleton. It does not cover all API calls, just those
    requested up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway.

    :param gateway_id: Gateway ID
    :param url: URL of the mPRM
    .. todo:: Make __instance a dict to handle multiple gateways at the same time
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


    def __init__(self, gateway_id: str, url: str):
        if self.__class__.__instance is not None:
            raise SyntaxError(f"Please use {self.__class__.__name__}.get_instance() to reuse the connection to the backend.")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = Gateway(gateway_id)
        self._mydevolo = Mydevolo.get_instance()
        self._session = requests.Session()
        self._data_id = 0
        self._mprm_url = url
        self._local_ip = None

        self.__class__.__instance = self


    def create_connection(self):
        """ Create session, either locally or via cloud. """
        if self._local_ip:
            self._gateway.local_connection = True
            self.get_local_session()
        elif self._gateway.external_access and not self._mydevolo.maintenance:
            self.get_remote_session()
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is not possible.")
            raise ConnectionError("Cannot connect to gateway.")

    def detect_gateway_in_lan(self):
        """ Detects a gateway in local network and check if it is the desired one. """
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[self._on_service_state_change])
        self._logger.info("Searching for gateway in LAN")
        start_time = time.time()
        while not time.time() > start_time + 3 and self._local_ip is None:
            for mdns_name in zeroconf.cache.entries():
                self._try_local_connection(mdns_name)
            else:
                time.sleep(0.05)
        threading.Thread(target=zeroconf.close).start()
        return self._local_ip

    def extract_data_from_element_uid(self, uid: str) -> dict:
        """
        Returns data from an element UID using an RPC call.

        :param uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :return: Data connected to the element UID, payload so to say
        """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self.post(data)
        return response.get("result").get("items")[0]

    def get_all_devices(self) -> dict:
        """
        Get all devices.

        :return: Dict with all devices and their properties.
        """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self.post(data)
        return response.get("result").get("items")[0].get("properties").get("deviceUIDs")

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

    def get_name_and_element_uids(self, uid: str):
        """
        Returns the name, all element UIDs and the device model of the given device UID.

        :param uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self.post(data)
        properties = response.get("result").get("items")[0].get("properties")
        return properties

    def get_remote_session(self):
        """ Connect to the gateway remotely. """
        self._logger.info("Connecting to gateway via cloud")
        try:
            self._session.get(self._gateway.full_url, timeout=15)
        except json.JSONDecodeError:
            raise MprmDeviceCommunicationError("Gateway is offline.") from None

    def post(self, data: dict) -> dict:
        """
        Communicate with the RPC interface.

        :param data: Data to be send
        :return: Response to the data
        """
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


    def _on_service_state_change(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        """ Service handler for Zeroconf state changes. """
        if state_change is ServiceStateChange.Added:
            zeroconf.get_service_info(service_type, name)

    def _try_local_connection(self, mdns_name: DNSRecord):
        """ Try to connect to an MDNS hostname. If connection was successful, save local IP. """
        try:
            ip = socket.inet_ntoa(mdns_name.address)
            if mdns_name.key.startswith("devolo-homecontrol") and \
                requests.get("http://" + ip + "/dhlp/port/full",
                             auth=(self._gateway.local_user, self._gateway.local_passkey),
                             timeout=0.5).status_code == requests.codes.ok:
                self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                self._local_ip = ip
        except (OSError, AttributeError):
            # OSError: Got IPv6 address which isn't supported by socket.inet_ntoa and the gateway as well.
            # AttributeError: The MDNS entry does not provide address information
            pass


class MprmDeviceCommunicationError(Exception):
    """ Communicating to a device via mPRM failed """


class MprmDeviceNotFoundError(Exception):
    """ A device like this was not found """
