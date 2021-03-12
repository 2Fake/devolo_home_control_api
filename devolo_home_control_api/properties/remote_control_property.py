from datetime import datetime
from typing import Callable

from ..exceptions.device import WrongElementError
from .property import Property


class RemoteControlProperty(Property):
    """
    Object for remote controls. It stores the button state and additional information that help displaying the state in the
    right context.

    :param element_uid: Element UID, something like devolo.RemoteControl:hdm:ZWave:CBC56091/24#2
    :param setter: Method to call on setting the state
    :key key_count: Number of buttons this remote control has
    :type key_count: int
    :key key_pressed: Number of the button pressed
    :type key_pressed: int
    """

    def __init__(self, element_uid: str, setter: Callable, **kwargs: int):
        if not element_uid.startswith("devolo.RemoteControl"):
            raise WrongElementError(f"{element_uid} is not a remote control.")

        super().__init__(element_uid=element_uid)
        self._setter = setter

        self._key_pressed = kwargs.pop("key_pressed", 0)
        self.key_count = kwargs.pop("key_count", 0)

    @property
    def key_pressed(self) -> int:
        """ Multi level value. """
        return self._key_pressed

    @key_pressed.setter
    def key_pressed(self, key_pressed: int):
        """ Update value of the multilevel value and set point in time of the last_activity. """
        self._key_pressed = key_pressed
        self._last_activity = datetime.now()
        self._logger.debug("key_pressed of element_uid %s set to %s.", self.element_uid, key_pressed)

    def set(self, key_pressed: int):
        """
        Trigger a button press of a remote control like if the button was physically pressed.

        :param key_pressed: Number of the button to press
        """
        if key_pressed > self.key_count or key_pressed <= 0:
            raise ValueError(f"Set value {key_pressed} is invalid.")

        if self._setter(self.element_uid, key_pressed):
            self.key_pressed = key_pressed
            self._logger.debug("Remote Control property %s set to %s", self.element_uid, key_pressed)
