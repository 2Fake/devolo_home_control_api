from datetime import datetime
from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .sensor_property import SensorProperty


class BinarySensorProperty(SensorProperty):
    """
    Object for binary sensors. It stores the binary sensor state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySensor:hdm:ZWave:CBC56091/24
    :key state: State of the binary sensor
    :type state: bool
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith(("devolo.BinarySensor:",
                                       "devolo.MildewSensor:",
                                       "devolo.SirenBinarySensor:",
                                       "devolo.ShutterMovementFI:",
                                       "devolo.WarningBinaryFI:",)):
            raise WrongElementError(f"{element_uid} is not a Binary Sensor.")

        self._state = False
        self.state = kwargs.get("state", False)

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)


    @property
    def last_activity(self) -> datetime:
        """ Date and time the state of the binary sensor was last updated. """
        return super().last_activity

    @last_activity.setter
    def last_activity(self, timestamp: int):
        """ The gateway persists the last activity of some binary sensors. They can be initialized with that value. """
        if timestamp != -1:
            self._last_activity = datetime.utcfromtimestamp(timestamp / 1000)
            self._logger.debug(f"self.last_activity of element_uid {self.element_uid} set to {self._last_activity}.")

    @property
    def state(self) -> bool:
        """ State of the binary sensor. """
        return self._state

    @state.setter
    def state(self, state: bool):
        """ Update state of the binary sensor and set point in time of the last_activity. """
        self._state = state
        self._last_activity = datetime.now()
