import logging
import json
from devolo_home_control_api.devices.zwave import get_device_type_from_element_uid,get_device_uid_from_element_uid


class Updater:
    def __init__(self, devices, publisher):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._devices = devices
        self._publisher = publisher

    def update(self, message):
        def binary_switch():
            if message.get("properties").get("property.name") == "state":
                self.update_binary_switch_state(element_uid=message.get("properties").get("uid"),
                                                value=True if message.get("properties").get("property.value.new") == 1
                                                else False)

        def gateway_accessible():
            if message.get("properties").get("property.name") == "gatewayAccessible":
                self.update_gateway_state(accessible=message.get("properties").get("property.value.new").get("accessible"),
                                          online_sync=message.get("properties").get("property.value.new").get("onlineSync"))

        def meter():
            if message.get("properties").get("property.name") == "currentValue":
                self.update_consumption(element_uid=message.get("properties").get("uid"),
                                        consumption="current",
                                        value=message.get("properties").get("property.value.new"))
            elif message.get("properties").get("property.name") == "totalValue":
                self.update_consumption(element_uid=message.get("properties").get("uid"),
                                        consumption="total", value=message.get("properties").get("property.value.new"))

        def voltage_multi_level_sensor():
            self.update_voltage(element_uid=message.get("properties").get("uid"),
                                value=message.get("properties").get("property.value.new"))


        message_type = {"devolo.BinarySwitch": binary_switch,
                        "devolo.mprm.gw.GatewayAccessibilityFI": gateway_accessible,
                        "devolo.Meter": meter,
                        "devolo.VoltageMultiLevelSensor": voltage_multi_level_sensor}
        try:
            message_type[get_device_type_from_element_uid(message.get("properties").get("uid"))]()
        except KeyError:
            self._logger.debug(json.dumps(message, indent=4))


    def update_binary_switch_state(self, element_uid: str, value: bool):
        """
        Function to update the internal binary switch state of a device.
        If a value is given, e.g. from a websocket, the value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._devices.get(device_uid).binary_switch_property.get(element_uid).state = value
        self._logger.debug(f"Updating state of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_consumption(self, element_uid: str, consumption: str, value: float):
        """
        Function to update the internal consumption of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like , something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param consumption: current or total consumption
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        if consumption == "current":
            self._devices.get(device_uid).consumption_property.get(element_uid).current = value
        else:
            self._devices.get(device_uid).consumption_property.get(element_uid).total = value
        self._logger.debug(f"Updating {consumption} consumption of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_voltage(self, element_uid: str, value: float):
        """
        Function to update the internal voltage of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._devices.get(device_uid).voltage_property.get(element_uid).current = value
        self._logger.debug(f"Updating voltage of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_gateway_state(self, accessible: bool, online_sync: bool):
        """
        Function to update the gateway status. A gateway might go on- or offline while we listen to the websocket.

        :param accessible: Online state of the gateway
        :param online_sync: Sync state of the gateway
        """
        self._logger.debug(f"Updating status and state of gateway to status: {accessible} and state: {online_sync}")
        self._gateway.online = accessible
        self._gateway.sync = online_sync
