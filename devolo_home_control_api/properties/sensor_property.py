"""Generic Sensors."""
from abc import ABC
from datetime import tzinfo

from .property import Property


class SensorProperty(Property, ABC):
    """
    Abstract object for sensors. It stores the sensor and sub type.

    :param element_uid: Element UID
    :param tz: Timezone the last activity is recorded in
    :key sensor_type: Type of the sensor sensor, something like 'alarm'
    :type sensor_type: str
    :key sub_type: Subtype of the sensor, something like 'overload'
    :type sub_type: str
    """

    def __init__(self, element_uid: str, tz: tzinfo, **kwargs: str) -> None:
        """Initialize the sensor."""
        super().__init__(element_uid, tz)

        self.sensor_type: str = kwargs.pop("sensor_type", "")
        self.sub_type: str = kwargs.pop("sub_type", "")
