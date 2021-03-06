from datetime import datetime

from requests import Session

from ..backend.mprm_rest import MprmRest
from ..devices.gateway import Gateway
from ..devices.zwave import get_device_uid_from_element_uid
from ..mydevolo import Mydevolo


class Property(MprmRest):
    """
    Base object for properties. It is not meant to use this directly.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param mydevolo: Mydevolo instance for talking to the devolo Cloud
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, gateway: Gateway, session: Session, mydevolo: Mydevolo, element_uid: str):
        self.element_uid = element_uid
        self.device_uid = get_device_uid_from_element_uid(element_uid)

        self._last_activity = datetime.fromtimestamp(0)  # Set last activity to 1.1.1970. Will be corrected on update.
        self._gateway = gateway
        self._session = session

        super().__init__(mydevolo_instance=mydevolo)


    @property
    def last_activity(self) -> datetime:
        """ Date and time the property was last updated. """
        return self._last_activity
