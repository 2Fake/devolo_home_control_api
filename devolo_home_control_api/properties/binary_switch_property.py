from requests import Session

from ..devices.gateway import Gateway
from .property import Property, WrongElementError


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :param state: State the switch has at time of creating this instance
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, state: bool):
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        self.state = state


    def set_binary_switch(self, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param state: True if switching on, False if switching off
        """
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "turnOn" if state else "turnOff", []]}
        response = self.post(data)
        if response.get("result").get("status") == 1:
            self.state = state
