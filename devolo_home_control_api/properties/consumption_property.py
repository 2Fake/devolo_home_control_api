from .property import Property


class ConsumptionProperty(Property):
    """
    Object for consumptions. It stores the current and total consumption and the corresponding units.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self.current_consumption = None
        self.current_consumption_unit = 'W'
        self.total_consumption = None
        self.total_consumption_unit = "kWh"
