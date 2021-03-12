import logging

from ..helper.string import camel_case_to_snake_case
from ..helper.uid import get_device_uid_from_element_uid
from ..mydevolo import Mydevolo


class Zwave:
    """
    Representing object for Z-Wave devices. Basically, everything can be stored in here. This is to be as flexible to gateway
    firmware changes as possible. So if new attributes appear or old ones are removed, they should be handled at least in
    reading them. Nevertheless, a few unwanted attributes are filtered.

    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    :key batteryLevel: Battery Level of the device in percent, -1 if mains powered
    :type batteryLevel: int
    :key elementUIDs: All element UIDs the device has
    :type elementUIDs: list
    :key manID: Manufacturer ID as registered at the Z-Wave alliance
    :type manID: str
    :key prodID: Product ID as registered at the Z-Wave alliance
    :type prodID: str
    :key prodTypeID: Product type ID as registered at the Z-Wave alliance
    :type prodTypeID: str
    :key status: Online status of the device
    :type status: int
    """

    def __init__(self, mydevolo_instance: Mydevolo, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = mydevolo_instance

        # Get important values
        self.battery_level = kwargs.pop("batteryLevel", -1)
        self.element_uids = kwargs.pop("elementUIDs")
        self.man_id = kwargs.pop("manID")
        self.prod_id = kwargs.pop("prodID")
        self.prod_type_id = kwargs.pop("prodTypeID")
        self.status = kwargs.pop("status", 1)

        # Remove unwanted values
        unwanted_value = [
            "icon",
            "itemName",
            "operationStatus",
            "zone",
            "zoneId",
        ]
        for value in unwanted_value:
            del kwargs[value]

        # Add all other values
        for key, value in kwargs.items():
            setattr(self, camel_case_to_snake_case(key), value)
        self.uid = get_device_uid_from_element_uid(self.element_uids[0])

        # Initialize additional Z-Wave information. Will be filled by Zwave.get_zwave_info, if available.
        z_wave_info_list = [
            "href",
            "manufacturer_id",
            "product_type_id",
            "product_id",
            "name",
            "brand",
            "identifier",
            "is_zwave_plus",
            "device_type",
            "zwave_version",
            "specific_device_class",
            "generic_device_class",
        ]
        for key in z_wave_info_list:
            setattr(self, key, None)

        # Remove battery properties, if device is mains powered.
        if self.battery_level == -1:
            delattr(self, "battery_level")
            delattr(self, "battery_low")

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
        self._logger.debug("Getting Z-Wave information for %s", self.uid)
        zwave_product = self._mydevolo.get_zwave_products(manufacturer=self.man_id,
                                                          product_type=self.prod_type_id,
                                                          product=self.prod_id)
        for key, value in zwave_product.items():
            setattr(self, camel_case_to_snake_case(key), value)

        # Clean up attributes which are now unwanted.
        clean_up_list = [
            "man_id",
            "prod_id",
            "prod_type_id",
            "statistics_uid",
            "wrong_device_paired",
        ]
        for attribute in clean_up_list:
            if hasattr(self, attribute):
                delattr(self, attribute)

    def is_online(self) -> bool:
        """
        Get the online state of a device.

        :return: False, if device is offline, else True
        """
        return self.status != 1
