import logging


class Zwave:
    """
    Representing object for Z-Wave devices.

    :param device_uid: Device UID, something like hdm:ZWave:CBC56091/24
    """

    def __init__(self, name: str, device_uid: str, zone: str, battery_level: int, icon: str, online_state: int):
        # TODO: Change to kwargs
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.zone = zone
        if battery_level != -1:
            self.battery_level = battery_level
        self.icon = icon
        self.device_uid = device_uid
        self.subscriber = None

        # Online state is returned as numbers. 1 --> Offline, 2 --> Online, 7 --> Not initialized
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
        return [*getattr(self, f"{name}_property").values()]


def get_device_type_from_element_uid(element_uid: str) -> str:
    """
    Return the device type of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    return element_uid.split(":", 1)[1].split("#")[0]
