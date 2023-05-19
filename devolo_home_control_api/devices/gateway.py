"""The devolo Home Control Central Unit."""
from __future__ import annotations

from datetime import timezone

from dateutil import tz

from devolo_home_control_api.exceptions import GatewayOfflineError
from devolo_home_control_api.mydevolo import Mydevolo


class Gateway:
    """
    Representing object for devolo Home Control Central Units. As it is a gateway from the IP world to the Z-Wave
    world, we call it that way. Nearly all attributes are delivered by my devolo.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    """

    def __init__(self, gateway_id: str, mydevolo_instance: Mydevolo) -> None:
        """Initialize the central unit."""
        self._mydevolo = mydevolo_instance

        details = self._mydevolo.get_gateway(gateway_id)

        self.id = details["gatewayId"]
        self.name = details.get("name")
        self.role = details.get("role")
        self.local_user = self._mydevolo.uuid()
        self.local_passkey = details["localPasskey"]
        self.external_access = details.get("externalAccess")
        self.timezone = tz.gettz(details["location"].get("timezone") or self._mydevolo.get_timezone()) or timezone.utc
        self.firmware_version = details.get("firmwareVersion")

        try:
            self.full_url: str | None = self._mydevolo.get_full_url(self.id)
        except GatewayOfflineError:
            self.full_url = None

        # Let's assume the gateway is connected remotely. Will be corrected as soon as a real connection is established.
        self.local_connection = False

        # Let's assume the gateway is offline. Will be corrected the twinkling of an eye.
        self.online = False
        self.sync = False

        self.zones: dict[str, str] = {}
        self.home_id = ""

        self._update_state(status=details.get("status", ""), state=details.get("state", ""))

    def update_state(self, online: bool | None = None) -> None:
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
        """Update the internal state."""
        self.online = status == "devolo.hc_gateway.status.online"
        self.sync = state == "devolo.hc_gateway.state.idle"
