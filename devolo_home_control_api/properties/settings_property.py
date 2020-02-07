from .property import Property, WrongElementError


class SettingsProperty(Property):
    """
    Object for settings. It stores the different settings.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid: str, **kwargs):
        if element_uid.split(".")[0] not in ["lis", "gds", "cps", "ps"]:
            raise WrongElementError()

        super().__init__(element_uid=element_uid)
        for key, value in kwargs.items():
            setattr(self, key, value)
