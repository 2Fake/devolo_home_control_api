"""Humidity Bars"""
from datetime import datetime

from ..exceptions.device import WrongElementError
from .sensor_property import SensorProperty


class HumidityBarProperty(SensorProperty):
    """
    Object for humidity bars. It stores the zone and the position inside that zone.

    :param element_uid: Fake element UID, something like devolo.HumidityBar:hdm:ZWave:CBC56091/24
    :key value: Position inside a zone
    :type value: int
    :key zone: Humidity zone from 0 (very dry) to 4 (very humid)
    :type zone: int
    """

    def __init__(self, element_uid: str, **kwargs) -> None:
        if not element_uid.startswith("devolo.HumidityBar:"):
            raise WrongElementError(f"{element_uid} is not a humidity bar.")

        super().__init__(element_uid=element_uid, **kwargs)

        self._value: int = kwargs.pop("value", 0)
        self.zone: int = kwargs.pop("zone", 0)

    @property
    def value(self) -> int:
        """Position inside a zone."""
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        """
        Update value and set point in time of the last_activity. As zone never changes without a value, just the value sets
        the last activity.
        """
        self._value = value
        self._last_activity = datetime.now()
        self._logger.debug("value of element_uid %s set to %s.", self.element_uid, value)
