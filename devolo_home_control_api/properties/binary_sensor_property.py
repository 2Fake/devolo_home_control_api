"""Binary Sensors."""
from datetime import datetime, timezone, tzinfo
from typing import Any

from devolo_home_control_api.exceptions import WrongElementError

from .sensor_property import SensorProperty


class BinarySensorProperty(SensorProperty):
    """
    Object for binary sensors. It stores the binary sensor state.

    :param element_uid: Element UID, something like devolo.BinarySensor:hdm:ZWave:CBC56091/24
    :param tz: Timezone the last activity is recorded in
    :key state: State of the binary sensor
    :type state: bool
    """

    def __init__(self, element_uid: str, tz: tzinfo, **kwargs: Any) -> None:
        """Initialize the binary sensor."""
        if not element_uid.startswith(
            ("devolo.BinarySensor:", "devolo.MildewSensor:", "devolo.ShutterMovementFI:", "devolo.WarningBinaryFI:")
        ):
            raise WrongElementError(element_uid, self.__class__.__name__)

        super().__init__(element_uid, tz, **kwargs)

        self._state: bool = kwargs.pop("state", False)

    @property
    def last_activity(self) -> datetime:
        """Date and time the state of the binary sensor was last updated."""
        return super().last_activity

    @last_activity.setter
    def last_activity(self, timestamp: int) -> None:
        """
        Set the last activity of the binary sensor. The gateway persists the last activity only for some of the binary sensors.
        They can be initialized with that value. The others stay with a default timestamp until first update.
        """
        if timestamp != -1:
            self._last_activity = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).replace(tzinfo=self._timezone)
            self._logger.debug("last_activity of element_uid %s set to %s.", self.element_uid, self._last_activity)

    @property
    def state(self) -> bool:
        """State of the binary sensor."""
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        """Update state of the binary sensor and set point in time of the last_activity."""
        self._state = state
        self._last_activity = datetime.now(tz=self._timezone)
        self._logger.debug("state of element_uid %s set to %s.", self.element_uid, state)
