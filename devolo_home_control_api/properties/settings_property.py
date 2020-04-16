from typing import Any

from requests import Session

from ..devices.gateway import Gateway
from .property import Property, WrongElementError


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
