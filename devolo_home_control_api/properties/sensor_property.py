from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import Property


class SensorProperty(Property):
    """
    Object for sensors. It stores the sensor and sub type

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID
    :key sensor_type: Type of the sensor sensor, something like 'alarm'
    :key sub_type: Subtype of the sensor, something like 'overload'
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self.sensor_type = kwargs.get("sensor_type")
        self.sub_type = kwargs.get("sub_type")
