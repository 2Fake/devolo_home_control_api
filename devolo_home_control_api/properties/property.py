import logging


class Property:
    """
    Base object for properties. It is not meant to use this directly.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.element_uid = element_uid


class WrongElementError(Exception):
    """ This element was not meant for this property """
