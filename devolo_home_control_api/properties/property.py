from datetime import datetime
from typing import Dict

from ..backend.mprm_rest import MprmRest
from ..devices.zwave import get_device_uid_from_element_uid


class Property(MprmRest):
    """
    Base object for properties. It is not meant to use this directly.

    :param connection: Collection of instances needed to communicate with the central unit
    :param element_uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
    """

    def __init__(self, connection: Dict, element_uid: str):
        self.element_uid = element_uid
        self.device_uid = get_device_uid_from_element_uid(element_uid)

        self._last_activity = datetime.fromtimestamp(0)  # Set last activity to 1.1.1970. Will be corrected on update.
        self._gateway = connection['gateway']
        self._session = connection['session']

        super().__init__(mydevolo_instance=connection['mydevolo'])


    @property
    def last_activity(self) -> datetime:
        """ Date and time the property was last updated. """
        return self._last_activity
