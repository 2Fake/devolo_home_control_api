from .property import Property, WrongElementError


class VoltageProperty(Property):
    """
    Object for voltages. It stores the current voltage and the corresponding unit.

    :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
    """

    def __init__(self, element_uid):
        if not element_uid.startswith("devolo.VoltageMultiLevelSensor:"):
            raise WrongElementError(f"{element_uid} is not a Voltage Sensor.")

        super().__init__(element_uid=element_uid)
        self.current = None
        self.current_unit = "V"
