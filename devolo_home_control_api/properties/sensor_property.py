from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import Property


class SensorProperty(Property):
    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        """
        Object for sensors. It stores the sensor and sub type

        :param sensor_type: Type of the sensor sensor. Something like 'alarm'
        :param sub_type: Subtype of the sensor. Something like 'overload'. Can be an empty string
        """
        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self.sensor_type = kwargs.get("sensor_type")
        self.sub_type = kwargs.get("sub_type")
