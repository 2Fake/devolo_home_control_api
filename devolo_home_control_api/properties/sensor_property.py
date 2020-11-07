from typing import Any, Dict

from .property import Property


class SensorProperty(Property):
    """
    Object for sensors. It stores the sensor and sub type.

    :param connection: Collection of instances needed to communicate with the central unit
    :param element_uid: Element UID
    :key sensor_type: Type of the sensor sensor, something like 'alarm'
    :type sensor_type: str
    :key sub_type: Subtype of the sensor, something like 'overload'
    :type sub_type: str
    """

    def __init__(self, connection: Dict, element_uid: str, **kwargs: Any):
        super().__init__(connection=connection, element_uid=element_uid)

        self.sensor_type = kwargs.get("sensor_type", "")
        self.sub_type = kwargs.get("sub_type", "")
