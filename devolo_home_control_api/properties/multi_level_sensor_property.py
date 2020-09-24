from datetime import datetime
from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .sensor_property import SensorProperty


class MultiLevelSensorProperty(SensorProperty):
    """
    Object for multi level sensors. It stores the multi level sensor state and additional information that help displaying the
    state in the right context.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#MultilevelSensor(1)
    :key value: Multi level value
    :type value: float
    :key unit: Unit of that value
    :type unit: int
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith(("devolo.DewpointSensor:",
                                       "devolo.MultiLevelSensor:",
                                       "devolo.SirenMultiLevelSensor:",
                                       "devolo.ValveTemperatureSensor",
                                       "devolo.VoltageMultiLevelSensor:")):
            raise WrongElementError(f"{element_uid} is not a Multi Level Sensor.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid, **kwargs)

        self._value = kwargs.get("value", 0.0)
        self._unit = ""
        self.unit = kwargs.get("unit", "")


    @property
    def unit(self) -> str:
        """ Human readable unit of the property. """
        return self._unit

    @unit.setter
    def unit(self, unit: int):
        """ Make the numeric unit human readable, if known. """
        units = {"dewpoint": {0: "°C", 1: "°F"},
                 "humidity": {0: "%", 1: "g/m³"},
                 "light": {0: "%", 1: "lx"},
                 "temperature": {0: "°C", 1: "°F"},
                 "Seismic Intensity": {0: ""},
                 "voltage": {0: "V", 1: "mV"}
                 }
        try:
            self._unit = units[self.sensor_type].get(unit, str(unit))
        except KeyError:
            self._unit = str(unit)
        self._logger.debug(f"Unit of {self.element_uid} set to '{self._unit}'.")

    @property
    def value(self) -> float:
        """ Multi level value. """
        return self._value

    @value.setter
    def value(self, value: float):
        """ Update value of the multilevel sensor and set point in time of the last_activity. """
        self._value = value
        self._last_activity = datetime.now()
