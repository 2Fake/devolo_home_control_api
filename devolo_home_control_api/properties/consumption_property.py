from datetime import datetime
from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import Property, WrongElementError


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24#2
    :param **kwargs: Consumption values valid at time of creating the instance
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.Meter:"):
            raise WrongElementError(f"{element_uid} is not a Meter.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        self.current = kwargs.get("current")
        self.current_unit = "W"
        self.total = kwargs.get("total")
        self.total_since = datetime.fromtimestamp(kwargs.get("total_since") / 1000)
        self.total_unit = "kWh"
