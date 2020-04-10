from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import WrongElementError
from .sensor_property import SensorProperty


class HumidityBarProperty(SensorProperty):
    """
    Object for humidity bars. It stores the zone and the position inside that zone.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Fake element UID, something like devolo.HumidityBar:hdm:ZWave:CBC56091/24
    :key value: Position inside a zone
    :key zone: Humidity zone from 0 (very dry) to 4 (very humid)
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.HumidityBar"):
            raise WrongElementError(f"{element_uid} is not a humidity bar.")

        self.value = kwargs.get("value", 0)
        self.zone = kwargs.get("zone", 0)

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
