"""Multi Level Switches."""
from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Any, Callable

from devolo_home_control_api.exceptions import WrongElementError

from .property import Property


class MultiLevelSwitchProperty(Property):
    """
    Object for multi level switches. It stores the multi level state and additional information that help displaying the state
    in the right context.

    :param element_uid: Element UID, something like devolo.Dimmer:hdm:ZWave:CBC56091/24#2
    :param tz: Timezone the last activity is recorded in
    :key value: Value the multi level switch has at time of creating this instance
    :type value: float
    :key switch_type: Type this switch is of, e.g. temperature
    :type switch_type: str
    :key max: Highest possible value, that can be set
    :type max: float
    :key min: Lowest possible value, that can be set
    :type min: float
    """

    def __init__(self, element_uid: str, tz: tzinfo, setter: Callable[[str, float], bool], **kwargs: Any) -> None:
        """Initialize the multi level switch."""
        if not element_uid.startswith(
            ("devolo.Blinds:", "devolo.Dimmer:", "devolo.MultiLevelSwitch:", "devolo.SirenMultiLevelSwitch:")
        ):
            raise WrongElementError(element_uid, self.__class__.__name__)

        super().__init__(element_uid, tz)
        self._setter = setter

        self._value: float = kwargs.pop("value", 0.0)
        self.switch_type: str = kwargs.pop("switch_type", "")
        self.max: float = kwargs.pop("max", 100.0)
        self.min: float = kwargs.pop("min", 0.0)

    @property
    def last_activity(self) -> datetime:
        """Date and time the state of the multi level switch was last updated."""
        return super().last_activity

    @last_activity.setter
    def last_activity(self, timestamp: int) -> None:
        """
        Set the last activity of the multi level switch. The gateway persists the last activity only for some of the multi
        level switchs. They can be initialized with that value. The others stay with a default timestamp until first update.
        """
        if timestamp != -1:
            self._last_activity = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).replace(tzinfo=self._timezone)
            self._logger.debug("last_activity of element_uid %s set to %s.", self.element_uid, self._last_activity)

    @property
    def unit(self) -> str | None:
        """Human readable unit of the property. Defaults to percent."""
        units = {
            "temperature": "°C",
            "tone": None,
        }
        return units.get(self.switch_type, "%")

    @property
    def value(self) -> float:
        """Multi level value."""
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        """Update value of the multilevel value and set point in time of the last_activity."""
        self._value = value
        self._last_activity = datetime.now(tz=self._timezone)
        self._logger.debug("Value of %s set to %s.", self.element_uid, value)

    def set(self, value: float) -> bool:
        """
        Set the multilevel switch of the given element_uid to the given value.

        :param value: Value to set
        """
        if value > self.max or value < self.min:
            raise ValueError(  # noqa: TRY003
                f"Set value {value} is too {'low' if value < self.min else 'high'}. "
                f"The min value is {self.min}. The max value is {self.max}"
            )

        if self._setter(self.element_uid, value):
            self.value = value
            return True
        return False
