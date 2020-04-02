from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import WrongElementError
from .sensor_property import SensorProperty


class VoltageProperty(SensorProperty):
    """
    Object for voltages. It stores the current voltage and the corresponding unit.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
    :key current: Voltage messured at the time of creating this instance
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.VoltageMultiLevelSensor:"):
            raise WrongElementError(f"{element_uid} is not a Voltage Sensor.")

        self.current = kwargs.get("current")
        self.current_unit = "V"

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
