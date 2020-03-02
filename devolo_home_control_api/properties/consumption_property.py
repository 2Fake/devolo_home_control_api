from datetime import datetime

from .property import Property, WrongElementError


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid: str, current: float, total: float, total_since: int):
        if not element_uid.startswith("devolo.Meter:"):
            raise WrongElementError(f"{element_uid} is not a Meter.")

        super().__init__(element_uid=element_uid)
        self.current = current
        self.current_unit = "W"
        self.total = total
        self.total_since = datetime.fromtimestamp(total_since / 1000)
        self.total_unit = "kWh"


    def fetch_consumption(self, consumption_type: str = "current") -> float:
        """
        Update and return the consumption, specified in consumption_type for the given uid.

        :param consumption_type: Current or total consumption
        :return: Consumption
        """
        if consumption_type not in ["current", "total"]:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        response = self.mprm.get_data_from_uid_list([self.element_uid])
        if consumption_type == "current":
            self.current = response.get("properties").get("currentValue")
            return self.current
        else:
            self.total = response.get("properties").get("totalValue")
            return self.total
