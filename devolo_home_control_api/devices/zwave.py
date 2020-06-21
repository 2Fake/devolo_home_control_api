import logging

from ..mydevolo import Mydevolo


class Zwave:
    """
    Representing object for Z-Wave devices. Basically, everything can be stored in here. This is to be as flexible to gateway
    firmware changes as possible. So if new attributes appear or old ones are removed, they should be handled at least in
    reading them. Nevertheless, a few unwanted attributes are filtered.
    """

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = Mydevolo.get_instance()

        for key, value in kwargs.items():
            setattr(self, key, value)
        self.uid = get_device_uid_from_element_uid(self.elementUIDs[0])

        # Initialize additional Z-Wave information. Will be filled by Zwave.get_zwave_info, if available.
        z_wave_info_list = ["href", "manufacturerId", "productTypeId", "productId", "name", "brand", "identifier",
                            "isZWavePlus", "deviceType", "zwaveVersion", "specificDeviceClass", "genericDeviceClass"]
        for key in z_wave_info_list:
            setattr(self, key, None)

        # Remove battery properties, if device is mains powered.
        if self.batteryLevel == -1:
            delattr(self, "batteryLevel")
            delattr(self, "batteryLow")


    def get_property(self, name: str) -> list:
        """
        Get element UIDs to a specified property.

        :param name: Name of the property we want to access
        :return: List of UIDs in this property
        :raises: AttributeError: The property does not exist in this device type
        """
        return [*getattr(self, f"{name}_property").values()]

    def get_zwave_info(self):
        """
        Get publicly available information like manufacturer or model from my devolo. For a complete list, please look at
        Zwave.__init__.
        """
        self._logger.debug(f"Getting Z-Wave information for {self.uid}")
        dict = self._mydevolo.get_zwave_products(manufacturer=self.manID,
                                                 product_type=self.prodTypeID,
                                                 product=self.prodID)
        for key, value in dict.items():
            setattr(self, key, value)

        # Clean up attributes which are now unwanted.
        clean_up_list = ["manID", "prodID", "prodTypeID"]
        for attribute in clean_up_list:
            if hasattr(self, attribute):
                delattr(self, attribute)

    def is_online(self) -> bool:
        """
        Get the online state of a device.

        :param uid: Device UID, something like hdm:ZWave:CBC56091/24
        :return: False, if device is offline, else True
        """
        return False if self.status == 1 else True


def get_device_type_from_element_uid(element_uid: str) -> str:
    """
    Return the device type of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]


def get_device_uid_from_setting_uid(setting_uid: str) -> str:
    """
    Return the device uid of the given setting UID.

    :param setting_uid: Setting UID, something like lis.hdm:ZWave:EB5A9F6C/2
    :return: Device UID, something like hdm:ZWave:EB5A9F6C/2
    """
    setting_uid = setting_uid.split(".", 1)[-1].split("#")[0]
    if setting_uid.endswith("secure"):
        return setting_uid.rsplit(":", 1)[0]
    return setting_uid


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    element_uid = element_uid.split(":", 1)[1].split("#")[0]
    if element_uid.endswith("secure"):
        return element_uid.rsplit(":", 1)[0]
    return element_uid
