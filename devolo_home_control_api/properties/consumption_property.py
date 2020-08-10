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
        self.current = kwargs.get("current")
        self.current_unit = "W"
        self.total = kwargs.get("total")
        self.total_unit = "kWh"

        # Set last activity to 1.1.1970. Will be corrected by ConsumptionProperty.total_since.
        self._total_since = datetime.fromtimestamp(0)
        self.total_since = kwargs.get("total_since", 0)


    @property
    def total_since(self) -> datetime:
        """ Date and time the binary sensor was last triggered. """
        return self._total_since

    @total_since.setter
    def total_since(self, timestamp: int):
        """ Convert a timestamp in millisecond to a datetime object. """
        self._total_since = datetime.fromtimestamp(timestamp / 1000)
        self._logger.debug(f"self.total_since of element_uid {self.element_uid} set to {self._total_since}.")
