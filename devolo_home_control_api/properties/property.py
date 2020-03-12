import logging

from ..backend.mprm_rest import MprmRest


class Property:
    """
    Base object for properties. It is not meant to use this directly.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, mprm: MprmRest, element_uid: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.element_uid = element_uid
        self.device_uid = element_uid.split(":", 1)[1].split("#")[0]
        self.mprm = MprmRest(gateway_id="1406126500001876", url="https://mprm-test.devolo.net")
        print(self.mprm)
        print(self.mprm._session)
        self.is_online = None


class WrongElementError(Exception):
    """ This element was not meant for this property. """
