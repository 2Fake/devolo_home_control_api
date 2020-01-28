import logging


class Zwave:
    """
    Representing object for Z-Wave devices connected to the devolo Home Control Central Unit

    :param device_uid: Device UID, something like hdm:ZWave:CBC56091/24
    """

    def __init__(self, name, device_uid, zone, battery_level, icon):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.zone = zone
        if battery_level != -1:
            self.battery_level = battery_level
        self.icon = icon
        self.device_uid = device_uid
        self.subscriber = None
