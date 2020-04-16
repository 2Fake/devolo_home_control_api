from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .sensor_property import SensorProperty
from .property import WrongElementError


class MildewSensorProperty(SensorProperty):
    """
    Object for mildew sensors. It stores the multilevel sensor value.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.MildewSensor:hdm:ZWave:CBC56091/24
    :key state: State of the mildew sensor
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.MildewSensor:"):
            raise WrongElementError(f"{element_uid} is not a Mildew Sensor.")

        self.state = kwargs.get("state")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
