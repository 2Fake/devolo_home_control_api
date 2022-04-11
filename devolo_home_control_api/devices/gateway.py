"""The devolo Home Control Central Unit"""
import logging
from typing import Dict, Optional

from ..mydevolo import Mydevolo


class Gateway:  # pylint: disable=too-few-public-methods
    """
    Representing object for devolo Home Control Central Units. As it is a gateway from the IP world to the Z-Wave
    world, we call it that way. Nearly all attributes are delivered by my devolo.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    """

    def __init__(self, gateway_id: str, mydevolo_instance: Mydevolo) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = mydevolo_instance

        details = self._mydevolo.get_gateway(gateway_id)

        self.id = details["gatewayId"]
        self.name = details.get("name")
        self.role = details.get("role")
        self.full_url = self._mydevolo.get_full_url(self.id)
        self.local_user = self._mydevolo.uuid()
        self.local_passkey = details["localPasskey"]
        self.external_access = details.get("externalAccess")
        self.firmware_version = details.get("firmwareVersion")

        # Let's assume the gateway is connected remotely. Will be corrected as soon as a real connection is established.
        self.local_connection = False

        # Let's assume the gateway is offline. Will be corrected the twinkling of an eye.
        self.online = False
        self.sync = False

        self.zones: Dict = {}
        self.home_id = ""

        self._update_state(status=details.get("status", ""), state=details.get("state", ""))

    def update_state(self, online: Optional[bool] = None) -> None:
        """
        Update the state of the gateway. If called without parameter, we will check my devolo.

        :param online: Detected state of the gateway
        """
        if online is None:
            details = self._mydevolo.get_gateway(self.id)
            self._update_state(status=details.get("status", ""), state=details.get("state", ""))
        else:
            self.online = online
            self.sync = online

    def _update_state(self, status: str, state: str) -> None:
        """Helper to update the state."""
        self.online = status == "devolo.hc_gateway.status.online"
        self.sync = state == "devolo.hc_gateway.state.idle"
