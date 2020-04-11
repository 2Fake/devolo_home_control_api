from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .sensor_property import SensorProperty
from .property import WrongElementError


class DewpointSensorProperty(SensorProperty):
    """
    Object for dewpoint sensors. It stores the multilevel sensor value.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.DewpointSensor:hdm:ZWave:CBC56091/24
    :key value: Multi level value
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.DewpointSensor:"):
            raise WrongElementError(f"{element_uid} is not a Dewpoint Sensor.")

        self.value = kwargs.get("value")
        self.unit = "°C"

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
