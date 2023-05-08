"""Binary Switches."""
from datetime import datetime, tzinfo
from typing import Callable

from devolo_home_control_api.exceptions import SwitchingProtected, WrongElementError

from .property import Property


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :param tz: Timezone the last activity is recorded in
    :param setter: Method to call on setting the state
    :key enabled: State of the remote protection setting
    :type enabled: bool
    :key state: State the switch has at time of creating this instance
    :type state: bool
    """

    def __init__(self, element_uid: str, tz: tzinfo, setter: Callable[[str, bool], bool], **kwargs: bool) -> None:
        """Initialize the binary switch."""
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(element_uid, self.__class__.__name__)

        super().__init__(element_uid, tz)
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
        self._last_activity = datetime.now(tz=self._timezone)
        self._logger.debug("State of %s set to %s.", self.element_uid, state)

    def set(self, state: bool) -> bool:
        """
        Set the binary switch of the given element_uid to the given state.

        :param state: True if switching on, False if switching off
        """
        if not self.enabled:
            raise SwitchingProtected

        if self._setter(self.element_uid, state):
            self.state = state
            return True
        return False
