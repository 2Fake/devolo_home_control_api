from datetime import datetime
from typing import Any, Optional

from requests import Session

from .property import Property
from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError


class MultiLevelSwitchProperty(Property):
    """
    Object for multi level switches. It stores the multi level state and additional information that help displaying the state
    in the right context.

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

        self._value = kwargs.get("value", 0.0)
        self.switch_type = kwargs.get("switch_type", "")
        self.max = kwargs.get("max", 100.0)
        self.min = kwargs.get("min", 0.0)


    @property
    def unit(self) -> Optional[str]:
        """ Human readable unit of the property. Defaults to percent. """
        units = {"temperature": "°C",
                 "tone": None}
        return units.get(self.switch_type, "%")

    @property
    def value(self) -> float:
        """ Multi level value. """
        return self._value

    @value.setter
    def value(self, value: float):
        """ Update value of the multilevel value and set point in time of the last_activity. """
        self._value = value
        self._last_activity = datetime.now()


    def set(self, value: float):
        """
        Set the multilevel switch of the given element_uid to the given value.

        :param value: Value to set
        """
        if value > self.max or value < self.min:
            raise ValueError(f"Set value {value} is too {'low' if value < self.min else 'high'}. The min value is {self.min}. \
                             The max value is {self.max}")
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "sendValue", [value]]}
        response = self.post(data)
        if response["result"].get("status") == 1:
            self.value = value
            self._logger.debug(f"Multi level switch property {self.element_uid} set to {value}")
        else:
            self._logger.debug(f"Something went wrong. Response to set command:\n{response}")
