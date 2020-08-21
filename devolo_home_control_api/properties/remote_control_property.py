from datetime import datetime
from typing import Any

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class RemoteControlProperty(Property):
    """
    Object for remote controls. It stores the button state and additional information that help displaying the state in the
    right context.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.RemoteControl:hdm:ZWave:CBC56091/24#2
    :key key_count: Number of buttons this remote control has
    :type key_count: int
    :key key_pressed: Number of the button pressed
    :type key_pressed: int
    """

    def __init__(self, gateway: Gateway, session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith("devolo.RemoteControl"):
            raise WrongElementError(f"{element_uid} is not a remote control.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self._key_pressed = kwargs.get("key_pressed", 0)
        self.key_count = kwargs.get("key_count", 0)


    @property
    def key_pressed(self) -> int:
        """ Multi level value. """
        return self._key_pressed

    @key_pressed.setter
    def key_pressed(self, key_pressed: float):
        """ Update value of the multilevel value and set point in time of the last_activity. """
        self._key_pressed = key_pressed
        self._last_activity = datetime.now()


    def set(self, key_pressed: int):
        """
        Trigger a button press of a remote control like if the button was physically pressed.

        :param key_pressed: Number of the button to press
        """
        if key_pressed > self.key_count or key_pressed <= 0:
            raise ValueError(f"Set value {key_pressed} is invalid.")

        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "pressKey", [key_pressed]]}
        self.post(data)
        self.key_pressed = key_pressed
        self._logger.debug(f"Remote Control property {self.element_uid} set to {key_pressed}")
