import json
import logging
from datetime import datetime
from typing import Any

from ..devices.gateway import Gateway
from ..devices.zwave import get_device_type_from_element_uid, get_device_uid_from_element_uid
from .publisher import Publisher


class Updater:
    """
    The Updater takes care of new states and values of devices and sends them to the Publisher object. Using methods in here
    do not effect the real device states.

    :param devices: List of devices to await updates for
    :param gateway: Instance of a Gateway object
    :param publisher: Instance of a Publisher object
    """

    def __init__(self, devices: dict, gateway: Gateway, publisher: Publisher):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = gateway
        self._publisher = publisher

        self.devices = devices
        self.on_device_change = None


    def update(self, message: dict):
        """
        Update states and values depending on the message type.

        :param message: Message to process
        """
        message_type = {"devolo.BinarySensor": self._binary_sensor,
                        "devolo.BinarySwitch": self._binary_switch,
                        "devolo.DeviceEvents": self._device_events,
                        "devolo.DevicesPage": self._device_change,
                        "devolo.DewpointSensor": self._dewpoint,
                        "devolo.HumidityBarValue": self._humidity_bar,
                        "devolo.HumidityBarZone": self._humidity_bar,
                        "devolo.mprm.gw.GatewayAccessibilityFI": self._gateway_accessible,
                        "devolo.Meter": self._meter,
                        "devolo.MildewSensor": self._mildew,
                        "devolo.MultiLevelSensor": self._multi_level_sensor,
                        "devolo.VoltageMultiLevelSensor": self._voltage_multi_level_sensor,
                        "hdm": self._device_online_state}
        try:
            message_type[get_device_type_from_element_uid(message.get("properties").get("uid"))](message)
        except KeyError:
            self._logger.debug(json.dumps(message, indent=4))

    def update_binary_sensor_state(self, element_uid: str, value: bool):
        """
        Update the binary switch state of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: True for on, False for off
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices.get(device_uid).binary_sensor_property.get(element_uid).state = value
        self._logger.debug(f"Updating state of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_binary_switch_state(self, element_uid: str, value: bool):
        """
        Update the binary switch state of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: True for on, False for off
        """
        if element_uid.split(".")[-2] == "smartGroup":
            # We ignore if a group is switched. We get the information separated for every device.
            return
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices.get(device_uid).binary_switch_property.get(element_uid).state = value
        self._logger.debug(f"Updating state of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_consumption(self, element_uid: str, consumption: str, value: float):
        """
        Update the consumption of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.Meter:hdm:ZWave:CBC56091/24
        :param consumption: current or total consumption
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        if consumption == "current":
            self.devices.get(device_uid).consumption_property.get(element_uid).current = value
        else:
            self.devices.get(device_uid).consumption_property.get(element_uid).total = value
        self._logger.debug(f"Updating {consumption} consumption of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_device_online_state(self, device_uid: str, value: int):
        """
        Update the device's online state. The value is written into the internal dict.

        :param device_uid: Device UID, something like hdm:ZWave:CBC56091/24#2
        :param value: 1 for online, all other numbers are treated as offline
        """
        self._logger.debug(f"Updating device online state of {device_uid} to {value}")
        self.devices.get(device_uid).status = value
        self._publisher.dispatch(device_uid, (device_uid, value))

    def update_dewpoint_sensor(self, element_uid: str, value: float):
        """
        Update the dewpoint sensor value externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.DewpointSensor:hdm:ZWave:CBC56091/24
        :param value: Value to be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")
        self.devices.get(device_uid).dewpoint_sensor_property.get(element_uid).value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_gateway_state(self, accessible: bool, online_sync: bool):
        """
        Update the gateway status externally. A gateway might go on- or offline while we listen to the websocket.

        :param accessible: Online state of the gateway
        :param online_sync: Sync state of the gateway
        """
        self._logger.debug(f"Updating status and state of gateway to status: {accessible} and state: {online_sync}")
        self._gateway.online = accessible
        self._gateway.sync = online_sync

    def update_humidity_bar(self, element_uid: str, **kwargs: Any):
        """
        Update humidity bar zone or value inside that zone.

        :param element_uid: Fake element UID, something like devolo.HumidityBar:hdm:ZWave:CBC56091/24
        :key value: Position inside a zone
        :key zone: Humidity zone
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        if kwargs.get("zone") is not None:
            self.devices.get(device_uid).humidity_bar_property.get(element_uid).zone = kwargs.get("zone")
            self._logger.debug(f'Updating humidity bar zone of {element_uid} to {kwargs.get("zone")}')
        if kwargs.get("value") is not None:
            self.devices.get(device_uid).humidity_bar_property.get(element_uid).value = kwargs.get("value")
            self._logger.debug(f'Updating humidity bar value of {element_uid} to {kwargs.get("value")}')
        self._publisher.dispatch(device_uid, (element_uid,
                                              self.devices.get(device_uid).humidity_bar_property.get(element_uid).zone,
                                              self.devices.get(device_uid).humidity_bar_property.get(element_uid).value))

    def update_mildew_sensor(self, element_uid: str, state: bool):
        """
        Update the mildew sensor state externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.MildewSensor:hdm:ZWave:CBC56091/24
        :param state: State to be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {state}")
        self.devices.get(device_uid).mildew_sensor_property.get(element_uid).state = state
        self._publisher.dispatch(device_uid, (element_uid, state))

    def update_multi_level_sensor(self, element_uid: str, value: float):
        """
        Update the multi level sensor value externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param value: Value to be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")
        self.devices.get(device_uid).multi_level_sensor_property.get(element_uid).value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_total_since(self, element_uid: str, total_since: datetime):
        """
        Update the point in time, the total consumption of a device was reset.

        :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param total_since: Point in time, the total consumption was reset
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices.get(device_uid).consumption_property.get(element_uid).total_since = total_since
        self._logger.debug(f"Updating total since of {element_uid} to {total_since}")
        self._publisher.dispatch(device_uid, (element_uid, total_since))

    def update_voltage(self, element_uid: str, value: float):
        """
        Update the voltage of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices.get(device_uid).voltage_property.get(element_uid).current = value
        self._logger.debug(f"Updating voltage of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_sensor(self, message: dict):
        """ Update a binary sensor's state. """
        if message.get("properties").get("property.value.new") is not None:
            self.update_binary_sensor_state(element_uid=message.get("properties").get("uid"),
                                            value=bool(message.get("properties").get("property.value.new")))

    def _binary_switch(self, message: dict):
        """ Update a binary switch's state. """
        if message.get("properties").get("property.name") == "state" and \
                message.get("properties").get("property.value.new") is not None:
            self.update_binary_switch_state(element_uid=message.get("properties").get("uid"),
                                            value=bool(message.get("properties").get("property.value.new")))

    def _current_consumption(self, property: dict):
        """ Update current consumption. """
        self.update_consumption(element_uid=property.get("uid"),
                                consumption="current",
                                value=property.get("property.value.new"))

    def _device_change(self, message: dict):
        """ Call method if a new device appears or an old one disappears. """
        if not callable(self.on_device_change):
            self._logger.error("on_device_change is not set.")
            return
        if type(message.get("properties").get("property.value.new")) == list \
           and message.get("properties").get("uid") == "devolo.DevicesPage":
            self.on_device_change(uids=message.get("properties").get("property.value.new"))

    def _device_events(self, message: dict):
        """ If an operation was not successful, we need to correct our internal state. """
        properties = {"properties": message.get("properties").get("property.value.new")}
        properties.get("properties")["uid"] = properties.get("properties").get("widgetElementUID")
        if get_device_type_from_element_uid(properties.get("properties").get("widgetElementUID")) == "devolo.BinarySwitch":
            properties.get("properties")["property.name"] = "state"
            properties.get("properties")["property.value.new"] = int(properties.get("properties").get("data"))
        self.update(properties)

    def _device_online_state(self, message: dict):
        """ Update the device's online state. """
        if message.get("properties").get("property.name") == "status":
            self.update_device_online_state(device_uid=message.get("properties").get("uid"),
                                            value=message.get("properties").get("property.value.new"))

    def _dewpoint(self, message: dict):
        """ Update a dewpoint sensor. """
        self.update_dewpoint_sensor(element_uid=message.get("properties").get("uid"),
                                    value=message.get("properties").get("property.value.new"))

    def _gateway_accessible(self, message: dict):
        """ Update the gateway's state. """
        if message.get("properties").get("property.name") == "gatewayAccessible":
            self.update_gateway_state(accessible=message.get("properties").get("property.value.new").get("accessible"),
                                      online_sync=message.get("properties").get("property.value.new").get("onlineSync"))

    def _humidity_bar(self, message: dict):
        """ Update a humidity bar. """
        fake_element_uid = f'devolo.HumidityBar:{message.get("properties").get("uid").split(":", 1)[1]}'
        if message.get("properties").get("uid").startswith("devolo.HumidityBarZone"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     zone=message.get("properties").get("property.value.new"))
        elif message.get("properties").get("uid").startswith("devolo.HumidityBarValue"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     value=message.get("properties").get("property.value.new"))

    def _meter(self, message: dict):
        """ Update a meter value. """
        property_name = {"currentValue": self._current_consumption,
                         "totalValue": self._total_consumption,
                         "sinceTime": self._since_time}

        property_name[message.get("properties").get("property.name")](message.get("properties"))

    def _mildew(self, message: dict):
        """ Update a mildew sensor. """
        self.update_mildew_sensor(element_uid=message.get("properties").get("uid"),
                                  state=bool(message.get("properties").get("property.value.new")))

    def _multi_level_sensor(self, message: dict):
        """ Update a multi level sensor. """
        self.update_multi_level_sensor(element_uid=message.get("properties").get("uid"),
                                       value=message.get("properties").get("property.value.new"))

    def _since_time(self, property: dict):
        """ Update point in time the total consumption was reset. """
        self.update_total_since(element_uid=property.get("uid"),
                                total_since=property.get("property.value.new"))

    def _total_consumption(self, property: dict):
        """ Update total consumption. """
        self.update_consumption(element_uid=property.get("uid"),
                                consumption="total",
                                value=property.get("property.value.new"))

    def _voltage_multi_level_sensor(self, message: dict):
        """ Update a voltage value. """
        self.update_voltage(element_uid=message.get("properties").get("uid"),
                            value=message.get("properties").get("property.value.new"))
