"""A Z-Wave device."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from devolo_home_control_api.helper import camel_case_to_snake_case, get_device_uid_from_element_uid
from devolo_home_control_api.mydevolo import Mydevolo

if TYPE_CHECKING:
    from devolo_home_control_api.properties import (
        BinarySensorProperty,
        BinarySwitchProperty,
        ConsumptionProperty,
        HumidityBarProperty,
        MultiLevelSensorProperty,
        MultiLevelSwitchProperty,
        RemoteControlProperty,
        SettingsProperty,
    )
    from devolo_home_control_api.properties.property import Property


class Zwave:
    """
    Representing object for Z-Wave devices. Basically, everything can be stored in here. This is to be as flexible to gateway
    firmware changes as possible. So if new attributes appear or old ones are removed, they should be handled at least in
    reading them. Nevertheless, a few unwanted attributes are filtered.

    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    :key batteryLevel: Battery Level of the device in percent, -1 if mains powered
    :type batteryLevel: int
    :key elementUIDs: All element UIDs the device has
    :type elementUIDs: List[str]
    :key manID: Manufacturer ID as registered at the Z-Wave alliance
    :type manID: str
    :key prodID: Product ID as registered at the Z-Wave alliance
    :type prodID: str
    :key prodTypeID: Product type ID as registered at the Z-Wave alliance
    :type prodTypeID: str
    :key status: Online status of the device
    :type status: int
    """

    binary_sensor_property: dict[str, BinarySensorProperty]
    binary_switch_property: dict[str, BinarySwitchProperty]
    consumption_property: dict[str, ConsumptionProperty]
    humidity_bar_property: dict[str, HumidityBarProperty]
    settings_property: dict[str, SettingsProperty]
    multi_level_sensor_property: dict[str, MultiLevelSensorProperty]
    multi_level_switch_property: dict[str, MultiLevelSwitchProperty]
    remote_control_property: dict[str, RemoteControlProperty]

    brand: str
    device_model_uid: str
    device_type: str
    href: str
    identifier: str
    is_zwave_plus: bool
    name: str
    manufacturer_id: str
    pending_operations: bool
    product_id: str
    product_type_id: str
    zwave_version: str

    def __init__(self, mydevolo_instance: Mydevolo, **kwargs: Any) -> None:
        """Initialize a Z-Wave device."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = mydevolo_instance

        # Get important values
        self.battery_level = kwargs.pop("batteryLevel", -1)
        self.battery_low = kwargs.pop("batteryLow", False)
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

    def get_property(self, name: str) -> list[Property]:
        """
        Get element UIDs to a specified property.

        :param name: Name of the property we want to access
        :return: List of UIDs in this property
        :raises: AttributeError: The property does not exist in this device type
        """
        return [*getattr(self, f"{name}_property").values()]

    def get_zwave_info(self) -> None:
        """
        Get publicly available information like manufacturer or model from my devolo. For a complete list, please look at
        Zwave.__init__.
        """
        self._logger.debug("Getting Z-Wave information for %s", self.uid)
        zwave_product = self._mydevolo.get_zwave_products(
            manufacturer=self.man_id, product_type=self.prod_type_id, product=self.prod_id
        )
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
