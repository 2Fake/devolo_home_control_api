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
        self.external_access = details.get("externalAccess")
        self.status = details.get("status")
        self.state = details.get("state")
        self.firmware_version = details.get("firmwareVersion")


    @property
    def full_url(self):
        """ The full URL is used to get a valid remote session """
        if self._full_url is None:
            # TODO: Catch errors like gateway offline
            self._full_url = self._mydevolo.get_full_url(self.id)
            self._logger.debug(f"Setting full URL to {self._full_url}")
        return self._full_url
