from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import WrongElementError
from .sensor_property import SensorProperty


class BinarySensorProperty(SensorProperty):
    """
    Object for binary sensors. It stores the binary sensor state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySensor:hdm:ZWave:CBC56091/24
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.BinarySensor:"):
            raise WrongElementError(f"{element_uid} is not a Binary Sensor.")

        self.state = kwargs.get("state")
        kwargs.pop("state")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
