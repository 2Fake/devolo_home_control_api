from requests import Session
from typing import Any

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class RemoteControlProperty(Property):
    """

    """

    def __init__(self, gateway: Gateway, session, element_uid: str, **kwargs: Any):
        """

        :param gateway:
        :param session:
        :param element_uid:
        :param kwargs:
        """
        if not element_uid.startswith("devolo.RemoteControl"):
            raise WrongElementError(f"{element_uid} is not a remote control.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self.key_count = kwargs.get("key_count")
        self.key_pressed = kwargs.get("key_pressed")
