from .property import Property


class VoltageProperty(Property):
    """
    Object for voltages. It stores the current voltage and the corresponding unit.

    :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
    """

    def __init__(self, element_uid):
        super().__init__(element_uid=element_uid)
        self.current = None
        self.current_unit = "V"