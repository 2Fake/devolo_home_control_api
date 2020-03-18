from requests import Session

from ..backend.mprm_rest import MprmRest
from ..devices.gateway import Gateway


class Property(MprmRest):
    """
    Base object for properties. It is not meant to use this directly.

    :param gateway: Instance of a Gateway object
    :param session: Instance of a requests.Session object
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, gateway: Gateway, session: Session, element_uid: str):
        self.element_uid = element_uid
        self.device_uid = element_uid.split(":", 1)[1].split("#")[0]
        self.is_online = None
        self._gateway = gateway
        self._session = session
        super().__init__()


class WrongElementError(Exception):
    """ This element was not meant for this property. """
