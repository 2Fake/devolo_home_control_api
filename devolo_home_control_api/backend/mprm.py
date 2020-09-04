import socket
import sys
import time
from json import JSONDecodeError
from threading import Thread
from typing import Optional

import requests
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from ..exceptions.gateway import GatewayOfflineError
from .mprm_websocket import MprmWebsocket


class Mprm(MprmWebsocket):
    """
    The abstract Mprm object handles the connection to the devolo Cloud (remote) or the gateway in your LAN (local). Either
    way is chosen, depending on detecting the gateway via mDNS.

    :param zeroconf_instance: Zeroconf instance to be potentially reused
    """

    def __init__(self, zeroconf_instance: Optional[Zeroconf]):
        super().__init__()

        self._token_url = {}

        self.detect_gateway_in_lan(zeroconf_instance)
        self.create_connection()


    def create_connection(self):
        """
        Create session, either locally or remotely via cloud. The remote case has two conditions, that both need to be
        fulfilled: Remote access must be allowed and my devolo must not be in maintenance mode.
        """
        if self._local_ip:
            self.gateway.local_connection = True
            self.get_local_session()
        elif self.gateway.external_access and not self._mydevolo.maintenance():
            self.get_remote_session()
        else:
            self._logger.error("Cannot connect to gateway. No gateway found in LAN and external access is not possible.")
            raise ConnectionError("Cannot connect to gateway.")

    def detect_gateway_in_lan(self, zeroconf_instance):
        """
        Detect a gateway in local network via mDNS and check if it is the desired one. Unfortunately, the only way to tell is
        to try a connection with the known credentials. If the gateway is not found within 3 seconds, it is assumed that a
        remote connection is needed.

        :param zeroconf_instance: Zeroconf instance to be potentially reused
        """
        zeroconf = zeroconf_instance or Zeroconf()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[self._on_service_state_change])
        self._logger.info("Searching for gateway in LAN.")
        start_time = time.time()
        while not time.time() > start_time + 3 and self._local_ip is None:
            time.sleep(0.05)

        Thread(target=browser.cancel, name=f"{__class__.__name__}.browser_cancel").start()
        if not zeroconf_instance:
            Thread(target=zeroconf.close, name=f"{__class__.__name__}.zeroconf_close").start()

        return self._local_ip

    def get_local_session(self):
        """
        Connect to the gateway locally. Calling a special portal URL on the gateway returns a second URL with a token. Calling
        that URL establishes the connection.
        """
        self._logger.info("Connecting to gateway locally.")
        self._session.url = "http://" + self._local_ip
        self._logger.debug(f"Session URL set to 'http://{self._local_ip}'")
        try:
            self._token_url = self._session.get(self._session.url + "/dhlp/portal/full",
                                                auth=(self.gateway.local_user, self.gateway.local_passkey), timeout=5).json()
            self._logger.debug(f"Got a token URL: {self._token_url}")
        except JSONDecodeError:
            self._logger.error("Could not connect to the gateway locally.")
            self._logger.debug(sys.exc_info())
            raise GatewayOfflineError("Gateway is offline.") from None
        except requests.exceptions.ConnectTimeout:
            self._logger.error("Timeout during connecting to the gateway.")
            self._logger.debug(sys.exc_info())
            raise
        self._session.get(self._token_url.get('link'))

    def get_remote_session(self):
        """
        Connect to the gateway remotely. Calling the known portal URL is enough in this case.
        """
        self._logger.info("Connecting to gateway via cloud.")
        try:
            self._session.get(self.gateway.full_url, timeout=15)
        except JSONDecodeError:
            self._logger.error("Could not connect to the gateway remotely.")
            self._logger.debug(sys.exc_info())
            raise GatewayOfflineError("Gateway is offline.") from None


    def _on_service_state_change(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        """ Service handler for Zeroconf state changes. """
        if state_change is ServiceStateChange.Added:
            service_info = zeroconf.get_service_info(service_type, name)
            if service_info.server.startswith("devolo-homecontrol"):
                self._try_local_connection(service_info.addresses)

    def _try_local_connection(self, addresses: list):
        """ Try to connect to an mDNS hostname. If connection was successful, save local IP address. """
        for address in addresses:
            ip = socket.inet_ntoa(address)
            if requests.get("http://" + ip + "/dhlp/port/full",
                            auth=(self.gateway.local_user, self.gateway.local_passkey),
                            timeout=0.5).status_code == requests.codes.ok:
                self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                self._local_ip = ip
