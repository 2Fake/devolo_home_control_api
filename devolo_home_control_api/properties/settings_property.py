from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from ..exceptions.device import WrongElementError
from .property import Property


class SettingsProperty(Property):
    """
    Object for settings. Basically, everything can be stored in here as long as there is a corresponding functional item on
    the gateway. This is to be as flexible to gateway firmware changes as possible. So if new attributes appear or old ones
    are removed, they should be handled at least in reading them. Nevertheless, a few unwanted attributes are filtered.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    :param **kwargs: Any setting, that shall be available in this object
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str, **kwargs: Any):
        if not element_uid.startswith(("acs", "bas", "bss", "cps", "gds", "lis", "mas",
                                       "mss", "ps", "sts", "stmss", "trs", "vfs")):
            raise WrongElementError()

        super().__init__(gateway=gateway, session=session, element_uid=element_uid)
        for key, value in kwargs.items():
            setattr(self, key, value)

        if element_uid.startswith("gds"):
            self.zone = self._gateway.zones[self.zone_id]

        setter_method = {"bas": self._set_bas,
                         "gds": self._set_gds,
                         "lis": self._set_lis,
                         "mss": self._set_mss,
                         "ps": self._set_ps,
                         "trs": self._set_trs,
                         "vfs": self._set_lis
                         }

        # Depending on the type of setting property, this will create a callable named "set".
        # However, this methods are not working, if the gateway is connected locally, yet.
        self.set = setter_method.get(element_uid.split(".")[0])

        # Clean up attributes which are unwanted.
        clean_up_list = ["device_uid"]

        for attribute in clean_up_list:
            delattr(self, attribute)


    def _set_bas(self, value: bool):
        """
        Set a binary async setting. This is e.g. the muted setting of a siren or the three way switch setting of a dimmer.

        :param value: New state
        """
        self.value = value
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [value]]}
        self.post(data)

    def _set_gds(self, **kwargs: Any):
        """
        Set one or more general device setting.

        :key events_enabled: Show events in diary
        :type events_enabled: bool
        :key icon: New icon name
        :type icon: string
        :key name: New device name
        :type name: string
        :key zone_id: New zone_id (ATTENTION: This is NOT the name of the location)
        :type events_enabled: string
        """
        allowed = ["events_enabled", "icon", "name", "zone_id"]
        for item in allowed:
            setattr(self, item, kwargs.get(item, getattr(self, item)))
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [{"events_enabled": self.events_enabled,
                                                       "icon": self.icon,
                                                       "name": self.name,
                                                       "zone_id": self.zone_id}]]}
        self.post(data)

    def _set_lis(self, led_setting: bool):
        """
        Set led settings.

        :param led_setting: LED indication setting
        """
        self.led_setting = led_setting
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.led_setting]]}
        self.post(data)

    def _set_mss(self, motion_sensitivity: int):
        """
        Set motion sensitivity.

        :param motion_sensitivity: Integer for the motion sensitivity setting.
        """
        if not 0 <= motion_sensitivity <= 100:
            raise ValueError("Value must be between 0 and 100")
        self.motion_sensitivity = motion_sensitivity
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.motion_sensitivity]]}
        self.post(data)

    def _set_ps(self, **kwargs):
        """
        Set one or both protection settings.

        :key local_switching: Allow local switching
        :type local_switching: bool
        :key remote_switching: Allow local switching
        :type remote_switching: bool
        """
        allowed = ["local_switching", "remote_switching"]
        [setattr(self, item, kwargs.get(item, getattr(self, item))) for item in allowed]
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [{"localSwitch": self.local_switching,
                                                       "remoteSwitch": self.remote_switching}]]}
        self.post(data)

    def _set_trs(self, temp_report: bool):
        """
        Set temperature report setting.

        :param temp_report: Boolean of the target value
        """
        self.temp_report = temp_report
        data = {"method": "FIM/invokeOperation",
                "params": [self.element_uid, "save", [self.temp_report]]}
        self.post(data)
