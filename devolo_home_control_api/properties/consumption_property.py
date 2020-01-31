from .property import Property, WrongElementError


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid):
        if not element_uid.startswith("devolo.Meter:"):
            raise WrongElementError(f"{element_uid} is not a Meter.")

        super().__init__(element_uid=element_uid)
        self.current = None
        self.current_unit = "W"
        self.total = None
        self.total_since = None
        self.total_unit = "kWh"
