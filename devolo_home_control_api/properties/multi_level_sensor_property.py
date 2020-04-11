from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .sensor_property import SensorProperty
from .property import WrongElementError


class MultiLevelSensorProperty(SensorProperty):
    """
    Object for multi level sensors. It stores the multi level sensor state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#MultilevelSensor(1)
    :key value: Multi level value
    :key unit: Unit of that value
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.MultiLevelSensor:"):
            raise WrongElementError(f"{element_uid} is not a Multi Level Sensor.")

        self.value = kwargs.get("value")
        self.unit = kwargs.get("unit")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)
