from datetime import datetime
from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import SwitchingProtected, WrongElementError
from .property import Property


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :key enabled: State of the remote protection setting
    :key state: State the switch has at time of creating this instance
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self._state = kwargs.get("state", False)
        self.enabled = kwargs.get("enabled", False)


    @property
    def state(self) -> bool:
        """ State of the binary sensor. """
        return self._state

    @state.setter
    def state(self, state: bool):
        """ Update state of the binary sensor and set point in time of the last_activity. """
        self._state = state
        self._last_activity = datetime.now()


    def set(self, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param state: True if switching on, False if switching off
        """
        if not self.enabled:
            raise SwitchingProtected("This device is protected against remote switching.")

        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "turnOn" if state else "turnOff", []]}
        response = self.post(data)
        if response["result"].get("status") == 1:
            self.state = state
            self._logger.debug(f"Binary switch property {self.element_uid} set to {state}")
        else:
            self._logger.debug(f"Something went wrong. Response to set command:\n{response}")
