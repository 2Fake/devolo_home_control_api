from .property import Property, WrongElementError


class SettingsProperty(Property):
    """
    Object for settings. It stores the different settings.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid, **kwargs):
        """

        :param kwargs:
        """
        super().__init__(element_uid=element_uid)
        for key, value in kwargs.items():
            if key == "led_setting":
                self.led_setting = value