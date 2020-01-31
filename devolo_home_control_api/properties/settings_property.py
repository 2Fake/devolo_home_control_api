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
        if element_uid.split(".")[0] not in ["lis", "gds", "cps", "ps"]:
            raise WrongElementError()
        for key, value in kwargs.items():
            if key == "led_setting":
                self.led_setting = value
            elif key == "events_enabled":
                self.events_enabled = value
            elif key == "param_changed":
                self.param_changed = value
            elif key == "local_switching":
                self.local_switching = value
            elif key == "remote_switching":
                self.remote_switching = value
