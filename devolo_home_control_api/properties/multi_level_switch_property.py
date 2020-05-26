from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class MultiLevelSwitchProperty(Property):
    """
    Object for multi level switches. It stores the multi level state

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.Dimmer:hdm:ZWave:CBC56091/24#2
    :key value: Value the multi level switch has at time of creating this instance
    :type value: float
    :key switch_type: Type this switch is of, e.g. temperature
    :type switch_type: string
    :key max: Highest possible value, that can be set
    :type max: float
    :key min: Lowest possible value, that can be set
    :type min: float
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith(("devolo.Blinds:",
                                       "devolo.Dimmer:",
                                       "devolo.MultiLevelSwitch:",
                                       "devolo.SirenMultiLevelSwitch:")):
            raise WrongElementError(f"{element_uid} is not a multi level switch.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)

        self.value = kwargs.get("value")
        self.switch_type = kwargs.get("switch_type")
        self.max = kwargs.get("max", 100)
        self.min = kwargs.get("min", 0)


    @property
    def unit(self) -> str:
        """ Human readable unit of the property. """
        units = {"temperature": "°C",
                 "tone": None}
        return units.get(self.switch_type, "%")


    def set(self, value: float):
        if value > self.max or value < self.min:
            raise ValueError(f"Set value {value} is too {'low' if value < self.min else 'high'}. The min value is {self.min}. \
                             The max value is {self.max}")
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "sendValue", [value]]}
        response = self.post(data)
        if response.get("result").get("status") == 1:
            self.value = value
