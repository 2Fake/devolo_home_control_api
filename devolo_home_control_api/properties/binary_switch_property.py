from .property import Property, WrongElementError
from ..backend.mprm_rest import MprmDeviceCommunicationError


class BinarySwitchProperty(Property):
    """
    Object for binary switches. It stores the binary switch state.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid: str):
        if not element_uid.startswith("devolo.BinarySwitch:"):
            raise WrongElementError(f"{element_uid} is not a Binary Switch.")

        super().__init__(element_uid=element_uid)
        self.state = None


    def fetch_binary_switch_state(self) -> bool:
        """
        Update and return the binary switch state for the given uid.

        :return: Binary switch state
        """
        response = self.mprm.extract_data_from_element_uid(self.element_uid)
        self.state = True if response.get("properties").get("state") == 1 else False
        return self.state

    def set_binary_switch(self, state: bool):
        """
        Set the binary switch of the given element_uid to the given state.

        :param state: True if switching on, False if switching off
        """
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "turnOn" if state else "turnOff", []]}
        response = self.mprm.post(data)
        if response.get("result").get("status") == 2 and not self.is_online(self.device_uid):
            raise MprmDeviceCommunicationError("The device is offline.")
        if response.get("result").get("status") == 1:
            self.state = state
        else:
            self._logger.info(f"Could not set state of device {self.device_uid}. Maybe it is already at this state.")
            self._logger.info(f"Target state is {state}. Actual state is {self.state}.")
