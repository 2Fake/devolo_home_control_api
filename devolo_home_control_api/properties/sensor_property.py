from abc import ABC

from .property import Property


class SensorProperty(Property, ABC):
    """
    Abstract object for sensors. It stores the sensor and sub type.

    :param connection: Collection of instances needed to communicate with the central unit
    :param element_uid: Element UID
    :key sensor_type: Type of the sensor sensor, something like 'alarm'
    :type sensor_type: str
    :key sub_type: Subtype of the sensor, something like 'overload'
    :type sub_type: str
    """

    def __init__(self, element_uid: str, **kwargs: str):
        super().__init__(element_uid=element_uid)

        self.sensor_type = kwargs.pop("sensor_type", "")
        self.sub_type = kwargs.pop("sub_type", "")
