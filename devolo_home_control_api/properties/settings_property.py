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
        self.setting_uid = element_uid
        for key, value in kwargs.items():
            setattr(self, key, value)


    def fetch_general_device_settings(self) -> tuple:
        """
        Update and return the events enabled setting. If a device shall report to the diary, this is true.

        :return: Events enabled or not
        """
        response = self.mprm.extract_data_from_element_uid(self.setting_uid)
        self.name = response.get("properties").get("name")
        self.icon = response.get("properties").get("icon")
        self.zone_id = response.get("properties").get("zoneID")
        self.events_enabled = response.get("properties").get("eventsEnabled")
        return self.name, self.icon, self.zone_id, self.events_enabled

    def fetch_led_setting(self) -> bool:
        """
        Update and return the led setting.

        :return: LED setting
        """
        response = self.mprm.extract_data_from_element_uid(self.setting_uid)
        self.led_setting = response.get("properties").get("led")
        return self.led_setting

    def fetch_param_changed_setting(self) -> bool:
        """
        Update and return the param changed setting.

        :param setting_uid: Settings UID to look at. Usually starts with cps.hdm.
        :return: True, if parameter was changed
        """
        response = self.mprm.extract_data_from_element_uid(self.setting_uid)
        self.param_changed = response.get("properties").get("paramChanged")
        return self.param_changed

    def fetch_protection_setting(self, protection_setting: str) -> bool:
        """
        Update and return the protection setting. There are only two protection settings: local and remote switching.

        :param protection_setting: Look at local or remote switching.
        :return: Switching is protected or not
        """
        if protection_setting not in ["local", "remote"]:
            raise ValueError("Only local and remote are possible protection settings")
        response = self.mprm.extract_data_from_element_uid(self.setting_uid)
        if protection_setting == "local":
            self.local_switching = response.get("properties").get("localSwitch")
            return self.local_switching
        else:
            self.remote_switching = response.get("properties").get("remoteSwitch")
            return self.remote_switching
