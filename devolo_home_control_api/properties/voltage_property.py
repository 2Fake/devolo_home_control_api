from requests import Session

from ..devices.gateway import Gateway
from .property import Property, WrongElementError


class VoltageProperty(Property):
    """
    Object for voltages. It stores the current voltage and the corresponding unit.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
    :param current: Voltage messured at the time of creating this instance
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, current: float):
        if not element_uid.startswith("devolo.VoltageMultiLevelSensor:"):
            raise WrongElementError(f"{element_uid} is not a Voltage Sensor.")

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        self.current = current
        self.current_unit = "V"


    def fetch_voltage(self) -> float:
        """
        Update and return the current voltage.

        :return: Voltage value
        """
        response = self.get_data_from_uid_list([self.element_uid])
        self.current = response.get("properties").get("value")
        return self.current
