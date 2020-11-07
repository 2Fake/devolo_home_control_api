from datetime import datetime
from typing import Any, Dict

from ..exceptions.device import WrongElementError
from .sensor_property import SensorProperty


class HumidityBarProperty(SensorProperty):
    """
    Object for humidity bars. It stores the zone and the position inside that zone.

    :param connection: Collection of instances needed to communicate with the central unit
    :param element_uid: Fake element UID, something like devolo.HumidityBar:hdm:ZWave:CBC56091/24
    :key value: Position inside a zone
    :type value: int
    :key zone: Humidity zone from 0 (very dry) to 4 (very humid)
    :type zone: int
    """

    def __init__(self, connection: Dict, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.HumidityBar:"):
            raise WrongElementError(f"{element_uid} is not a humidity bar.")

        self._value = kwargs.get("value", 0)
        self.zone = kwargs.get("zone", 0)

        super().__init__(connection=connection, element_uid=element_uid, **kwargs)


    @property
    def value(self) -> int:
        """ Position inside a zone. """
        return self._value

    @value.setter
    def value(self, value: int):
        """
        Update value and set point in time of the last_activity. As zone never changes without a value, just the value sets
        the last activity.
        """
        self._value = value
        self._last_activity = datetime.now()
