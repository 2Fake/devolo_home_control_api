import logging
from ..backend.mprm_websocket import MprmWebsocket


class Property:
    """
    Base object for properties. It is not meant to use this directly.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.element_uid = element_uid
        self.device_uid = element_uid.split(":", 1)[1].split("#")[0]
        self.mprm = MprmWebsocket.get_instance()
        self.is_online = None


class WrongElementError(Exception):
    """ This element was not meant for this property. """
