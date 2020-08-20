from datetime import datetime
from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24#2
    :key current: Consumption value valid at time of creating the instance
    :key total: Total consumption since last reset
    :key total_since: Timestamp in milliseconds of last reset
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.Meter:"):
            raise WrongElementError(f"{element_uid} is not a Meter.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        self._current = kwargs.get("current", 0.0)
        self.current_unit = "W"
        self._total = kwargs.get("total", 0.0)
        self.total_unit = "kWh"

        self._total_since = datetime.utcfromtimestamp(kwargs.get("total_since", 0) / 1000)


    @property
    def current(self) -> float:
        """ Consumption value. """
        return self._current

    @current.setter
    def current(self, current: float):
        """ Update current consumption and set point in time of the last_activity. """
        self._current = current
        self._last_activity = datetime.now()

    @property
    def total(self) -> float:
        """ Total consumption value. """
        return self._total

    @total.setter
    def total(self, total: float):
        """ Update total consumption and set point in time of the last_activity. """
        self._total = total
        self._last_activity = datetime.now()

    @property
    def total_since(self) -> datetime:
        """ Date and time the binary sensor was last triggered. """
        return self._total_since

    @total_since.setter
    def total_since(self, timestamp: int):
        """ Convert a timestamp in millisecond to a datetime object. """
        self._total_since = datetime.utcfromtimestamp(timestamp / 1000)
        self._logger.debug(f"self.total_since of element_uid {self.element_uid} set to {self._total_since}.")
