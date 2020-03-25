from requests import Session

from ..devices.gateway import Gateway
from .property import Property


class SensorProperty(Property):
    def __init__(self, gateway: Gateway, session: Session, element_uid: str, sensor_type: str, sub_type: str):
        """
        Object for sensors. It stores the sensor and sub type

        :param sensor_type: Type of the sensor sensor. Something like 'alarm'
        :param sub_type: Subtype of the sensor. Somethink like 'overload'. Can be an empty string
        """
        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self.sensor_type = sensor_type
        self.sub_type = sub_type

