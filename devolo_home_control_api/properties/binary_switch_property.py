"""Binary Switches"""
from datetime import datetime
from typing import Callable

from ..exceptions.device import SwitchingProtected, WrongElementError
from .property import Property


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :param setter: Method to call on setting the state
    :key enabled: State of the remote protection setting
    :type enabled: bool
    :key state: State the switch has at time of creating this instance
    :type state: bool
    """

    def __init__(self, element_uid: str, setter: Callable, **kwargs: bool) -> None:
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(element_uid=element_uid)
        self._setter = setter

        self._state: bool = kwargs.pop("state", False)
        self.enabled: bool = kwargs.pop("enabled", False)

    @property
    def state(self) -> bool:
        """State of the binary sensor."""
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        """Update state of the binary sensor and set point in time of the last_activity."""
        self._state = state
        self._last_activity = datetime.now()
        self._logger.debug("State of %s set to %s.", self.element_uid, state)

    def set(self, state: bool) -> None:
        """
        Set the binary switch of the given element_uid to the given state.

        :param state: True if switching on, False if switching off
        """
        if not self.enabled:
            raise SwitchingProtected("This device is protected against remote switching.")

        if self._setter(self.element_uid, state):
            self.state = state
