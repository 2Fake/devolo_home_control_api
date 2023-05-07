"""Multi Level Sensors."""
from datetime import datetime, tzinfo
from typing import Any

from devolo_home_control_api.exceptions import WrongElementError

from .sensor_property import SensorProperty


class MultiLevelSensorProperty(SensorProperty):
    """
    Object for multi level sensors. It stores the multi level sensor state and additional information that help displaying the
    state in the right context.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#MultilevelSensor(1)
    :param tz: Timezone the last activity is recorded in
    :key value: Multi level value
    :type value: float
    :key unit: Unit of that value
    :type unit: int
    """

    def __init__(self, element_uid: str, tz: tzinfo, **kwargs: Any) -> None:
        """Initialize the multi level sensor."""
        if not element_uid.startswith(
            (
                "devolo.DewpointSensor:",
                "devolo.MultiLevelSensor:",
                "devolo.ValveTemperatureSensor",
                "devolo.VoltageMultiLevelSensor:",
            )
        ):
            raise WrongElementError(element_uid, self.__class__.__name__)

        super().__init__(element_uid, tz, **kwargs)

        self._value: float = kwargs.pop("value", 0.0)
        self._unit: int = kwargs.pop("unit", 0)

    @property
    def unit(self) -> str:
        """Human readable unit of the property."""
        units = {
            "dewpoint": {0: "°C", 1: "°F"},
            "humidity": {0: "%", 1: "g/m³"},
            "light": {0: "%", 1: "lx"},
            "temperature": {0: "°C", 1: "°F"},
            "Seismic Intensity": {0: ""},
            "voltage": {0: "V", 1: "mV"},
        }
        try:
            return units[self.sensor_type].get(self._unit, str(self._unit))
        except KeyError:
            return str(self._unit)

    @property
    def value(self) -> float:
        """Multi level value."""
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        """Update value of the multilevel sensor and set point in time of the last_activity."""
        self._value = value
        self._last_activity = datetime.now(tz=self._timezone)
        self._logger.debug("value of element_uid %s set to %s.", self.element_uid, value)
