import logging


class Zwave:
    """
    Representing object for Z-Wave devices connected to the devolo Home Control Central Unit

    :param device_uid: Device UID, something like hdm:ZWave:CBC56091/24
    """

    def __init__(self, name: str, device_uid: str, zone: str, battery_level: int, icon: str, online_state: int):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.zone = zone
        if battery_level != -1:
            self.battery_level = battery_level
        self.icon = icon
        self.device_uid = device_uid
        self.subscriber = None

        # Online state is returned as numbers. 1 --> Offline, 2 --> Online, 7 (?) --> Not initialized
        if online_state == 1:
            self.online = "offline"
        elif online_state == 2:
            self.online = "online"
        else:
            self.online = "unknown state"
            self._logger.warning(f"Unknown state {online_state} for device {self.name}")

    def get_property(self, name: str) -> list:
        """
        Get element UIDs to a specified property.

        :param name: Name of the property we want to access
        :return: List of UIDs in this property
        :raises: AttributeError: The property does not exist in this device type
        """
        return [*getattr(self, f"{name}_property").keys()]
