import json
import logging
from typing import Any

from ..devices.gateway import Gateway
from ..helper.string import camel_case_to_snake_case
from ..helper.uid import get_device_type_from_element_uid, get_device_uid_from_element_uid, get_device_uid_from_setting_uid
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
        message_type = {"bas.hdm": self._binary_async,
                        "cps.hdm": self._parameter,
                        "gds.hdm": self._general_device,
                        "lis.hdm": self._led,
                        "vfs.hdm": self._led,
                        "devolo.BinarySensor": self._binary_sensor,
                        "devolo.BinarySwitch": self._binary_switch,
                        "devolo.Blinds": self._multi_level_switch,
                        "devolo.DeviceEvents": self._device_events,
                        "devolo.DevicesPage": self._device_change,
                        "devolo.Dimmer": self._multi_level_switch,
                        "devolo.DewpointSensor": self._multi_level_sensor,
                        "devolo.HumidityBarValue": self._humidity_bar,
                        "devolo.HumidityBarZone": self._humidity_bar,
                        "devolo.mprm.gw.GatewayAccessibilityFI": self._gateway_accessible,
                        "devolo.Meter": self._meter,
                        "devolo.MildewSensor": self._binary_sensor,
                        "devolo.MultiLevelSensor": self._multi_level_sensor,
                        "devolo.MultiLevelSwitch": self._multi_level_switch,
                        "devolo.RemoteControl": self._remote_control,
                        "devolo.SirenBinarySensor": self._binary_sensor,
                        "devolo.SirenMultiLevelSensor": self._multi_level_sensor,
                        "devolo.SirenMultiLevelSwitch": self._multi_level_switch,
                        "devolo.VoltageMultiLevelSensor": self._multi_level_sensor,
                        "hdm": self._device_online_state}
        try:
            message_type[get_device_type_from_element_uid(message["properties"]["uid"])](message)
        except KeyError:
            self._logger.debug(json.dumps(message, indent=4))

    def update_binary_async_value(self, element_uid: str, value: bool):
        device_uid = get_device_uid_from_setting_uid(element_uid)
        try:
            self.devices[device_uid].settings_property[camel_case_to_snake_case(element_uid).split("#")[-1]].value = value
        except KeyError:
            # Siren setting is not initialized like others.
            self.devices[device_uid].settings_property["muted"].value = value
        self._logger.debug(f"Udating value of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_binary_sensor_state(self, element_uid: str, value: bool):
        """
        Update the binary switch state of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: True for on, False for off
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].binary_sensor_property[element_uid].state = value
        self._logger.debug(f"Updating state of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_binary_switch_state(self, element_uid: str, value: bool):
        """
        Update the binary switch state of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: True for on, False for off
        """
        if element_uid.split(".")[-2] == "smartGroup":
            # We ignore if a group is switched. We get the information separately for every device.
            return
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].binary_switch_property[element_uid].state = value
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
            self.devices[device_uid].consumption_property[element_uid].current = value
        else:
            self.devices[device_uid].consumption_property[element_uid].total = value
        self._logger.debug(f"Updating {consumption} consumption of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value, consumption))

    def update_device_online_state(self, device_uid: str, value: int):
        """
        Update the device's online state. The value is written into the internal dict.

        :param device_uid: Device UID, something like hdm:ZWave:CBC56091/24#2
        :param value: 1 for online, all other numbers are treated as offline
        """
        self._logger.debug(f"Updating device online state of {device_uid} to {value}")
        self.devices[device_uid].status = value
        self._publisher.dispatch(device_uid, (device_uid, value))

    def update_gateway_state(self, accessible: bool, online_sync: bool):
        """
        Update the gateway status externally. A gateway might go on- or offline while we listen to the websocket.

        :param accessible: Online state of the gateway
        :param online_sync: Sync state of the gateway
        """
        self._logger.debug(f"Updating status and state of gateway to status: {accessible} and state: {online_sync}")
        self._gateway.online = accessible
        self._gateway.sync = online_sync

    def update_general_device_settings(self, element_uid, **kwargs: str):
        device_uid = get_device_uid_from_setting_uid(element_uid)
        for key, value in kwargs.items():
            setattr(self.devices[device_uid].settings_property["general_device_settings"], key, value)
            self._logger.debug(f"Updating attribute: {key} of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (key, value))

    def update_humidity_bar(self, element_uid: str, **kwargs: Any):
        """
        Update humidity bar zone or value inside that zone.

        :param element_uid: Fake element UID, something like devolo.HumidityBar:hdm:ZWave:CBC56091/24
        :key value: Position inside a zone
        :type value: int
        :key zone: Humidity zone
        :type zone: int
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        if kwargs.get("zone") is not None:
            self.devices[device_uid].humidity_bar_property[element_uid].zone = kwargs["zone"]
            self._logger.debug(f'Updating humidity bar zone of {element_uid} to {kwargs["zone"]}')
        if kwargs.get("value") is not None:
            self.devices[device_uid].humidity_bar_property[element_uid].value = kwargs["value"]
            self._logger.debug(f'Updating humidity bar value of {element_uid} to {kwargs["value"]}')
        self._publisher.dispatch(device_uid, (element_uid,
                                              self.devices[device_uid].humidity_bar_property[element_uid].zone,
                                              self.devices[device_uid].humidity_bar_property[element_uid].value))

    def update_led(self, element_uid: str, value: bool):
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}.")
        self.devices[device_uid].settings_property["led"].led_setting = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_multi_level_sensor(self, element_uid: str, value: float):
        """
        Update the multi level sensor value externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param value: Value to be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_multi_level_switch(self, element_uid: str, value: float):
        """
        Update the multi level switch value externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.MultiLevelSwitch* or devolo.Dimmer* or devolo.Blinds*
        :param value: Value to be set
        """
        if element_uid.split(".")[-2] == "smartGroup":
            # We ignore if a group is switched. We get the information separately for every device.
            return
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")
        self.devices[device_uid].multi_level_switch_property[element_uid].value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_parameter(self, element_uid: str, param_changed: bool):
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["param_changed"].param_chaned = param_changed
        self._logger.debug(f"Updating param_changed of {element_uid} to {param_changed}")
        self._publisher.dispatch(device_uid, (element_uid, param_changed))

    def update_remote_control(self, element_uid: str, key_pressed: int):
        """
        Update the remote control button state externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.RemoteControl:hdm:ZWave:CBC56091/24#2
        :param key_pressed: Button that was pressed
        """
        # The message for the diary needs to be ignored
        if key_pressed is not None:
            device_uid = get_device_uid_from_element_uid(element_uid)
            old_key_pressed = self.devices[device_uid].remote_control_property[element_uid].key_pressed
            self.devices[device_uid].remote_control_property[element_uid].key_pressed = key_pressed
            self._logger.debug(f"Updating remote control of {element_uid}.\
                               Key {f'pressed: {key_pressed}' if key_pressed != 0 else f'released: {old_key_pressed}'}")
            self._publisher.dispatch(device_uid, (element_uid, key_pressed))

    def update_total_since(self, element_uid: str, total_since: int):
        """
        Update the point in time, the total consumption of a device was reset.

        :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param total_since: Point in time, the total consumption was reset
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].consumption_property[element_uid].total_since = total_since
        self._logger.debug(f"Updating total since of {element_uid} to {total_since}")
        self._publisher.dispatch(device_uid, (element_uid, total_since))

    def update_voltage(self, element_uid: str, value: float):
        """
        Update the voltage of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
        :param value: Value so be set
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._logger.debug(f"Updating voltage of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_async(self, message: dict):
        if type(message["properties"].get("property.value.new")) not in [dict, list]:
            self.update_binary_async_value(element_uid=message["properties"]["uid"],
                                           value=bool(message["properties"]["property.value.new"]))

    def _binary_sensor(self, message: dict):
        """ Update a binary sensor's state. """
        if message["properties"]["property.value.new"] is not None:
            self.update_binary_sensor_state(element_uid=message["properties"]["uid"],
                                            value=bool(message["properties"]["property.value.new"]))

    def _binary_switch(self, message: dict):
        """ Update a binary switch's state. """
        if message["properties"]["property.name"] == "state" and \
                message["properties"]["property.value.new"] is not None:
            self.update_binary_switch_state(element_uid=message["properties"]["uid"],
                                            value=bool(message["properties"]["property.value.new"]))

    def _current_consumption(self, property: dict):
        """ Update current consumption. """
        self.update_consumption(element_uid=property["uid"],
                                consumption="current",
                                value=property["property.value.new"])

    def _device_change(self, message: dict):
        """ Call method if a new device appears or an old one disappears. """
        if not callable(self.on_device_change):
            self._logger.error("on_device_change is not set.")
            return
        if type(message["properties"]["property.value.new"]) == list \
           and message["properties"]["uid"] == "devolo.DevicesPage":
            self.on_device_change(uids=message["properties"]["property.value.new"])

    def _device_events(self, message: dict):
        """ If an operation was not successful, we need to correct our internal state. """
        properties = {"properties": message["properties"]["property.value.new"]}
        if type(properties["properties"]) is dict:
            properties['properties']['uid'] = properties["properties"]["widgetElementUID"]
            if get_device_type_from_element_uid(properties['properties']['uid']) == "devolo.BinarySwitch":
                # TODO: Check, if we need to handle other device types than BinarySwitch on unsuccessful operations
                properties['properties']['property.name'] = "state"
                properties['properties']['property.value.new'] = int(properties["properties"]["data"])
            self.update(properties)

    def _device_online_state(self, message: dict):
        """ Update the device's online state. """
        if message["properties"]["property.name"] == "status":
            self.update_device_online_state(device_uid=message["properties"]["uid"],
                                            value=message["properties"]["property.value.new"])

    def _gateway_accessible(self, message: dict):
        """ Update the gateway's state. """
        if message["properties"]["property.name"] == "gatewayAccessible":
            self.update_gateway_state(accessible=message["properties"]["property.value.new"]["accessible"],
                                      online_sync=message["properties"]["property.value.new"]["onlineSync"])

    def _general_device(self, message: dict):
        self.update_general_device_settings(element_uid=message["properties"]["uid"],
                                            events_enabled=message["properties"]["property.value.new"]["eventsEnabled"],
                                            icon=message["properties"]["property.value.new"]["icon"],
                                            name=message["properties"]["property.value.new"]["name"],
                                            zone_id=message["properties"]["property.value.new"]["zoneID"])

    def _humidity_bar(self, message: dict):
        """ Update a humidity bar. """
        fake_element_uid = f'devolo.HumidityBar:{message["properties"]["uid"].split(":", 1)[1]}'
        if message["properties"]["uid"].startswith("devolo.HumidityBarZone"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     zone=message["properties"]["property.value.new"])
        elif message["properties"]["uid"].startswith("devolo.HumidityBarValue"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     value=message["properties"]["property.value.new"])

    def _led(self, message: dict):
        self.update_led(element_uid=message["properties"]["uid"],
                        value=message["properties"]["property.value.new"])

    def _meter(self, message: dict):
        """ Update a meter value. """
        property_name = {"currentValue": self._current_consumption,
                         "totalValue": self._total_consumption,
                         "sinceTime": self._since_time}

        property_name[message["properties"]["property.name"]](message["properties"])

    def _multi_level_sensor(self, message: dict):
        """ Update a multi level sensor. """
        self.update_multi_level_sensor(element_uid=message["properties"]["uid"],
                                       value=message["properties"]["property.value.new"])

    def _multi_level_switch(self, message: dict):
        """ Update a multi level switch. """
        if not isinstance(message["properties"]["property.value.new"], (list, dict, type(None))):
            self.update_multi_level_switch(element_uid=message["properties"]["uid"],
                                           value=message["properties"]["property.value.new"])

    def _parameter(self, message: dict):
        self.update_parameter(element_uid=message["properties"]["uid"],
                              param_changed=message["properties"]["property.value.new"])

    def _remote_control(self, message: dict):
        """ Update a remote control. """
        self.update_remote_control(element_uid=message["properties"]["uid"],
                                   key_pressed=message["properties"]["property.value.new"])

    def _since_time(self, property: dict):
        """ Update point in time the total consumption was reset. """
        self.update_total_since(element_uid=property["uid"],
                                total_since=property["property.value.new"])

    def _total_consumption(self, property: dict):
        """ Update total consumption. """
        self.update_consumption(element_uid=property["uid"],
                                consumption="total",
                                value=property["property.value.new"])

    def _voltage_multi_level_sensor(self, message: dict):
        """ Update a voltage value. """
        self.update_voltage(element_uid=message["properties"]["uid"],
                            value=message["properties"]["property.value.new"])
