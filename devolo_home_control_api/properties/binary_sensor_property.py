from requests import Session

from ..devices.gateway import Gateway
from .property import Property, WrongElementError


class BinarySensorProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs):
        if not element_uid.startswith("devolo.BinarySensor:"):
            raise WrongElementError(f"{element_uid} is not a Binary Sensor.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.state = bool(self.state)
