"""mPRM communication"""
import contextlib
import socket
import sys
import time
from abc import ABC
from http import HTTPStatus
from json import JSONDecodeError
from threading import Thread
from typing import List, Optional
from urllib.parse import urlsplit

import requests
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from ..exceptions.gateway import GatewayOfflineError
from .mprm_websocket import MprmWebsocket


class Mprm(MprmWebsocket, ABC):
    """
    The abstract Mprm object handles the connection to the devolo Cloud (remote) or the gateway in your LAN (local). Either
    way is chosen, depending on detecting the gateway via mDNS.
    """

    def __init__(self) -> None:
        self._zeroconf: Optional[Zeroconf]

        super().__init__()

        self.detect_gateway_in_lan()
        self.create_connection()

    def create_connection(self) -> None:
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

    def detect_gateway_in_lan(self) -> str:
        """
        Detect a gateway in local network via mDNS and check if it is the desired one. Unfortunately, the only way to tell is
        to try a connection with the known credentials. If the gateway is not found within 3 seconds, it is assumed that a
        remote connection is needed.

        :return: Local IP of the gateway, if found
        """
        zeroconf = self._zeroconf or Zeroconf()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[self._on_service_state_change])
        self._logger.info("Searching for gateway in LAN.")
        start_time = time.time()
        while not time.time() > start_time + 3 and self._local_ip == "":
            time.sleep(0.05)

        Thread(target=browser.cancel, name=f"{self.__class__.__name__}.browser_cancel").start()
        if not self._zeroconf:
            Thread(target=zeroconf.close, name=f"{self.__class__.__name__}.zeroconf_close").start()

        return self._local_ip

    def get_local_session(self) -> bool:
        """
        Connect to the gateway locally. Calling a special portal URL on the gateway returns a second URL with a token. Calling
        that URL establishes the connection.
        """
        self._logger.info("Connecting to gateway locally.")
        self._url = f"http://{self._local_ip}"
        self._logger.debug("Session URL set to '%s'", self._url)
        try:
            connection = self._session.get(
                f"{self._url}/dhlp/portal/full", auth=(self.gateway.local_user, self.gateway.local_passkey), timeout=5
            )

        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            self._logger.error("Could not connect to the gateway locally.")
            self._logger.debug(sys.exc_info())
            raise GatewayOfflineError("Gateway is offline.") from None

        # After a reboot we can connect to the gateway but it answers with a 503 if not fully started.
        if not connection.ok:
            self._logger.error("Could not connect to the gateway locally.")
            self._logger.debug("Gateway start-up is not finished, yet.")
            raise GatewayOfflineError("Gateway is offline.") from None

        token_url = connection.json()["link"]
        self._logger.debug("Got a token URL: %s", token_url)

        self._session.get(token_url)
        return True

    def get_remote_session(self) -> bool:
        """
        Connect to the gateway remotely. Calling the known portal URL is enough in this case.
        """
        self._logger.info("Connecting to gateway via cloud.")
        try:
            url = urlsplit(self._session.get(self.gateway.full_url, timeout=15).url)
            self._url = f"{url.scheme}://{url.netloc}"
            self._logger.debug("Session URL set to '%s'", self._url)
        except JSONDecodeError:
            self._logger.error("Could not connect to the gateway remotely.")
            self._logger.debug(sys.exc_info())
            raise GatewayOfflineError("Gateway is offline.") from None
        return True

    def _on_service_state_change(
        self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
    ) -> None:
        """Service handler for Zeroconf state changes."""
        if state_change is ServiceStateChange.Added:
            service_info = zeroconf.get_service_info(service_type, name)
            if service_info and service_info.server.startswith("devolo-homecontrol"):
                with contextlib.suppress(requests.exceptions.ReadTimeout), contextlib.suppress(
                    requests.exceptions.ConnectTimeout
                ):
                    self._try_local_connection(service_info.addresses)

    def _try_local_connection(self, addresses: List[bytes]) -> None:
        """Try to connect to an mDNS hostname. If connection was successful, save local IP address."""
        for address in addresses:
            ip = socket.inet_ntoa(address)
            if (
                requests.get(
                    f"http://{ip}/dhlp/port/full", auth=(self.gateway.local_user, self.gateway.local_passkey), timeout=0.5
                ).status_code
                == HTTPStatus.OK
            ):
                self._logger.debug("Got successful answer from ip %s. Setting this as local gateway", ip)
                self._local_ip = ip
