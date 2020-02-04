import logging

from ..mydevolo import Mydevolo


class Gateway:
    """
    Representing object for devolo Home Control Central Units. As it is a gateway from the IP world to the Z-Wave
    world, we call it that way.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    """

    def __init__(self, gateway_id: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = Mydevolo.get_instance()
        self._full_url = None

        details = self._mydevolo.get_gateway(gateway_id)

        self.id = details.get("gatewayId")
        self.name = details.get("name")
        self.role = details.get("role")
        self.local_user = self._mydevolo.uuid
        self.local_passkey = details.get("localPasskey")
        self.local_connection = False
        self.external_access = details.get("externalAccess")
        self.firmware_version = details.get("firmwareVersion")

        self._update_state(status=details.get("status"), state=details.get("state"))


    @property
    def full_url(self):
        """ The full URL is used to get a valid remote session """
        if self._full_url is None:
            self._full_url = self._mydevolo.get_full_url(self.id)
            self._logger.debug(f"Setting full URL to {self._full_url}")
        return self._full_url


    def update_state(self, online: bool = None):
        """
        Update the state of the gateway. If called without parameter, we will check my devolo.

        :param online: Detected state of the gateway
        """
        if online is None:
            details = self._mydevolo.get_gateway(self.id)
            self._update_state(status=details.get("status"), state=details.get("state"))
        else:
            self.online = online
            self.sync = online


    def _update_state(self, status, state):
        """ Helper to update the state. """
        if status == "devolo.hc_gateway.status.online":
            self.online = True
        else:
            self.online = False
        if state == "devolo.hc_gateway.state.idle":
            self.sync = True
        else:
            self.sync = False
