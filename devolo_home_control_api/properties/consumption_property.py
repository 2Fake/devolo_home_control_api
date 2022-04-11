"""Consumptions"""
from datetime import datetime
from typing import Union

from ..exceptions.device import WrongElementError
from .property import Property


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24#2
    :key current: Consumption value valid at time of creating the instance
    :type current: float
    :key total: Total consumption since last reset
    :type total: float
    :key total_since: Timestamp in milliseconds of last reset
    :type total_since: int
    """

    def __init__(self, element_uid: str, **kwargs: Union[int, float]) -> None:
        if not element_uid.startswith("devolo.Meter:"):
            raise WrongElementError(f"{element_uid} is not a Meter.")

        super().__init__(element_uid=element_uid)

        self._current: float = kwargs.pop("current", 0.0)
        self.current_unit = "W"
        self._total: float = kwargs.pop("total", 0.0)
        self.total_unit = "kWh"
        self._total_since = datetime.utcfromtimestamp(kwargs.pop("total_since", 0) / 1000)

    @property
    def current(self) -> float:
        """Consumption value."""
        return self._current

    @current.setter
    def current(self, current: float) -> None:
        """Update current consumption and set point in time of the last_activity."""
        self._current = current
        self._last_activity = datetime.now()
        self._logger.debug("current of element_uid %s set to %s.", self.element_uid, current)

    @property
    def total(self) -> float:
        """Total consumption value."""
        return self._total

    @total.setter
    def total(self, total: float) -> None:
        """Update total consumption and set point in time of the last_activity."""
        self._total = total
        self._last_activity = datetime.now()
        self._logger.debug("total of element_uid %s set to %s.", self.element_uid, total)

    @property
    def total_since(self) -> datetime:
        """Date and time the binary sensor was last triggered."""
        return self._total_since

    @total_since.setter
    def total_since(self, timestamp: int) -> None:
        """Convert a timestamp in millisecond to a datetime object."""
        self._total_since = datetime.utcfromtimestamp(timestamp / 1000)
        self._logger.debug("total_since of element_uid %s set to %s.", self.element_uid, self._total_since)
