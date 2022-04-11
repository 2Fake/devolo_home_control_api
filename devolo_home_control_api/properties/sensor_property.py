"""Generic Sensors"""
from abc import ABC

from .property import Property


class SensorProperty(Property, ABC):  # pylint: disable=too-few-public-methods
    """
    Abstract object for sensors. It stores the sensor and sub type.

    :param connection: Collection of instances needed to communicate with the central unit
    :param element_uid: Element UID
    :key sensor_type: Type of the sensor sensor, something like 'alarm'
    :type sensor_type: str
    :key sub_type: Subtype of the sensor, something like 'overload'
    :type sub_type: str
    """

    def __init__(self, element_uid: str, **kwargs: str) -> None:
        super().__init__(element_uid=element_uid)

        self.sensor_type: str = kwargs.pop("sensor_type", "")
        self.sub_type: str = kwargs.pop("sub_type", "")
