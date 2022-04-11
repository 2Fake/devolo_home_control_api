"""Generic Properties"""
import logging
from abc import ABC
from datetime import datetime

from ..devices.zwave import get_device_uid_from_element_uid


class Property(ABC):  # pylint: disable=too-few-public-methods
    """
    Abstract base object for properties.

    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, element_uid: str) -> None:
        self.element_uid = element_uid
        self.device_uid = get_device_uid_from_element_uid(element_uid)

        self._logger = logging.getLogger(self.__class__.__name__)
        self._last_activity = datetime.fromtimestamp(0)  # Set last activity to 1.1.1970. Will be corrected on update.

    @property
    def last_activity(self) -> datetime:
        """Date and time the property was last updated."""
        return self._last_activity
