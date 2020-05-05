from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class SettingsProperty(Property):
    """
    Object for settings. It stores the different settings.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :param **kwargs: Any setting, that shall be available in this object
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if element_uid.split(".")[0] not in ["cps", "gds", "lis", "mss", "ps", "trs", "vfs"]:
            raise WrongElementError()

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        self.setting_uid = element_uid
        for key, value in kwargs.items():
            setattr(self, key, value)

        setter = {"cps": self.set_cps,
                  "gds": self.set_gds,
                  "lis": self.set_lis,
                  "mss": self.set_mss,
                  "ps": self.set_ps,
                  "trs": self.set_trs,
                  "vfs": self.set_vfs
                  }

        self.setter = setter.get(element_uid.split(".")[0])

    def set_cps(self):
        pass

    def set_gds(self, **kwargs):
        """
        Setter for general device settings.
        :param kwargs:
            events_enabled: Boolean of the target value for the diary entry of a device
            icon: String of the target icon.
            name: String of the target name.
            zone_id: String of target zone_id. ATTENTION: This is NOT the name of the location.
        :return:
        """
        allowed = ["events_enabled", "icon", "name", "zone_id"]
        [setattr(self, item, kwargs.get(item, getattr(self, item))) for item in allowed]
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [{"events_enabled": self.events_enabled,
                                                       "icon": self.icon,
                                                       "name": self.name,
                                                       "zone_id": self.zone_id}]]}
        self.post(data)

    def set_lis(self, target_value: bool):
        """
        Setter for led settings.
        :param target_value: Boolean of the led indication setting.
        """
        self.led_setting = target_value
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.led_setting]]}
        self.post(data)

    def set_mss(self, target_value: int):
        """
        Setter for motion sensitivity setting.
        :param target_value: Integer for the motion sensitivity setting.
        :raises WrongElementError: If target value is not in range of 0 to 100.
        """
        if not 0 <= target_value <= 100:
            raise WrongElementError("Value should be between 0 and 100")
        self.motion_sensitivity = target_value
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.motion_sensitivity]]}
        self.post(data)

    def set_ps(self, **kwargs):
        """
        Setter for the protection settings.
        :param: **kwargs:
            local_switching: Boolean of the target value for local switching
            remote_switching: Boolean of the target value for remote switching
        """
        allowed = ["local_switching", "remote_switching"]
        [setattr(self, item, kwargs.get(item, getattr(self, item))) for item in allowed]
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [{"localSwitch": self.local_switching,
                                                       "remoteSwitch": self.remote_switching}]]}
        self.post(data)

    def set_trs(self, target_value: bool):
        """
        Setter for temperature report setting.
        :param target_value: Boolean of the target value
        """
        self.temp_report = target_value
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.temp_report]]}
        self.post(data)

    def set_vfs(self, target_value):
        """
        Setter for visual feedback setting.
        :param target_value: Boolean of the target value
        """
        self.led_setting = target_value
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.led_setting]]}
        self.post(data)
