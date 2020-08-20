import json
import logging

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
        message_type = {"acs.hdm": self._automatic_calibration,
                        "bas.hdm": self._binary_async,
                        "bss.hdm": self._binary_sync,
                        "cps.hdm": self._parameter,
                        "gds.hdm": self._general_device,
                        "lis.hdm": self._led,
                        "ps.hdm": self._protection,
                        "stmss.hdm": self._multilevel_sync,
                        "sts.hdm": self._switch_type,
                        "trs.hdm": self._temperature,
                        "vfs.hdm": self._led,
                        "mss.hdm": self._multilevel_sync,
                        "devolo.BinarySensor": self._binary_sensor,
                        "devolo.BinarySwitch": self._binary_switch,
                        "devolo.Blinds": self._multi_level_switch,
                        "devolo.DevicesPage": self._device_change,
                        "devolo.Dimmer": self._multi_level_switch,
                        "devolo.DewpointSensor": self._multi_level_sensor,
                        "devolo.Grouping": self._grouping,
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
                        "devolo.ShutterMovementFI": self._binary_sensor,
                        "devolo.VoltageMultiLevelSensor": self._multi_level_sensor,
                        "devolo.WarningBinaryFI:": self._binary_sensor,
                        "hdm": self._device_online_state}

        if "property.name" in message["properties"] \
                and message['properties']['property.name'] == "pendingOperations" \
                and "smartGroup" not in message["properties"]["uid"]:
            self._pending_operations(message)
        else:
            message_type.get(get_device_type_from_element_uid(message['properties']['uid']), self._unknown)(message)

    def update_automatic_calibration(self, element_uid: str, calibration_status: bool):
        """
        Update automatic calibration setting of a device externally. The value is written into the internal dict.
        :param element_uid: Element UID, something like, acs.hdm:ZWave:F6BF9812/20
        :param calibration_status: Bool for the setting
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["automatic_calibration"].calibration_status = calibration_status
        self._logger.debug(f"Updating value of {element_uid} to {calibration_status}")
        self._publisher.dispatch(device_uid, (element_uid, calibration_status))

    def update_binary_async_setting(self, element_uid: str, value: bool):
        """
        Update binary async setting of a device externally. The value is written into the internal dict.

        :param element_uid: Element UID, something like, bas.hdm:ZWave:CBC56091/24#2
        :param value: True for setting set, False for setting not set
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        try:
            self.devices[device_uid].settings_property[camel_case_to_snake_case(element_uid).split("#")[-1]].value = value
        except KeyError:
            # Siren setting is not initialized like others.
            self.devices[device_uid].settings_property['muted'].value = value
        self._logger.debug(f"Updating value of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_binary_sync_setting(self, element_uid: str, value: bool):
        """
        Update binary sync setting of a device externally. The value is written into the internal dict.
        Actually we just know that the shutter has a property like this.

        :param element_uid: Element UID, something like, bss.hdm:ZWave:CBC56091/24#2
        :param value: True for inverted, False for default
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["movement_direction"].direction = value
        self._logger.debug(f"Updating value of {element_uid} to {value}")
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
        """
        Update general device settings externally.

        :param element_uid: Element UID, something like gds.hdm:ZWave:CBC56091/24
        :key events_enabled: Show events in the diary
        :type events_enabled: bool
        :key icon: Icon of the device
        :type icon: string
        :key name: Name of the device
        :type name: string
        :key zone_id: ID of the zone, also called room
        :type zone_id: string
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        for key, value in kwargs.items():
            setattr(self.devices[device_uid].settings_property['general_device_settings'], key, value)
            self._logger.debug(f"Updating attribute: {key} of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (key, value))

    def update_humidity_bar(self, element_uid: str, **kwargs: int):
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
            self.devices[device_uid].humidity_bar_property[element_uid].zone = kwargs['zone']
            self._logger.debug(f"Updating humidity bar zone of {element_uid} to {kwargs['zone']}")
        if kwargs.get("value") is not None:
            self.devices[device_uid].humidity_bar_property[element_uid].value = kwargs['value']
            self._logger.debug(f"Updating humidity bar value of {element_uid} to {kwargs['value']}")
        self._publisher.dispatch(device_uid, (element_uid,
                                              self.devices[device_uid].humidity_bar_property[element_uid].zone,
                                              self.devices[device_uid].humidity_bar_property[element_uid].value))

    def update_led(self, element_uid: str, value: bool):
        """
        Update led settings externally.

        :param element_uid: Element UID, something like lis.hdm:ZWave:CBC56091/24
        :param value: True for led on, false for led off
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}.")
        self.devices[device_uid].settings_property['led'].led_setting = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_multilevel_sync(self, element_uid: str, value: int):
        """
        Update multilevel sync settings externally.

        :param element_uid: Element UID, something like mss.hdm:ZWave:CBC56091/24
        :param value: Value (e.g. the tone for the siren) the setting is set to
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")

        # The devolo Siren uses multilevel sync settings for a different reason.
        if self.devices[device_uid].device_model_uid == "devolo.model.Siren":
            self.devices[device_uid].settings_property['tone'].tone = value

        # The shutter use multilevel sync settings for a different reason.
        elif self.devices[device_uid].device_model_uid in ("devolo.model.OldShutter", "devolo.model.Shutter"):
            self.devices[device_uid].settings_property['shutter_duration'].shutter_duration = value

        # Other devices are up to now always motion sensors.
        else:
            self.devices[device_uid].settings_property['motion_sensitivity'].motion_sensitivity = value

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
        """
        Update the setting, that stores if Z-Wave expert settings were used.

        :param element_uid: Element UID, something like cps.hdm:ZWave:CBC56091/24
        :param param_changed: True, if settings were used, otherwise false
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property['param_changed'].param_changed = param_changed
        self._logger.debug(f"Updating param_changed of {element_uid} to {param_changed}")
        self._publisher.dispatch(device_uid, (element_uid, param_changed))

    def update_pending_operations(self, element_uid: str, pending_operations: bool):
        """
        Update the pending operation attribute of a device.

        :param element_uid: Any kind of element UID, that represents a device property
        :param pending_operations: True, if operations are pending, otherwise false
        """
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating pending operations of device {device_uid} to {pending_operations}")
        self.devices[device_uid].pending_operations = pending_operations
        self._publisher.dispatch(device_uid, ("pending_operations", pending_operations))

    def update_protection(self, element_uid: str, name: str, value: bool):
        """
        Update the protection mode setting of a device.

        :param element_uid: Any kind of element UID, that represents a device property
        :param name: Either targetLocalSwitch to prevent local switching or targetRemoteSwitch to prevent remote switching
        :param value: True to prevent switching, false to allow switching
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        if name == "targetLocalSwitch":
            self.devices[device_uid].settings_property['protection'].local_switching = value
            self._logger.debug(f"Updating local switch protection of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value, "local_switching"))
        else:
            self.devices[device_uid].settings_property['protection'].remote_switching = value
            self._logger.debug(f"Updating remote switch protection of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value, "remote_switching"))

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

    def update_switch_type(self, element_uid: str, value: int):
        """
        Update switch type setting externally.

        :param element_uid: Element UID, something like sts.hdm:ZWave:F6BF9812/8
        :param value: Count of buttons
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property['switch_type'].value = value
        self.devices[device_uid].remote_control_property[f'devolo.RemoteControl:{device_uid}'].key_count = value
        self._logger.debug(f"Updating switch type of {device_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def update_temperature(self, element_uid: str, value: bool):
        """
        Update temperature report state externally.

        :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param value: True, if temperature reports shall be send, false otherwise
        """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property['temperature_report'].temp_report = value
        self._logger.debug(f"Updating temperature report of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

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

    def _automatic_calibration(self, message: dict):
        """ Update a automatic calibration message. """
        try:
            calibration_status = message["properties"]["property.value.new"]["status"]
            self.update_automatic_calibration(element_uid=message["properties"]["uid"],
                                              calibration_status=False if calibration_status == 2 else True)
        except (KeyError, TypeError):
            if type(message["properties"]["property.value.new"]) not in [dict, list]:
                self.update_automatic_calibration(element_uid=message["properties"]["uid"],
                                                  calibration_status=bool(message["properties"]["property.value.new"]))

    def _binary_async(self, message: dict):
        """ Update a binary async setting. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            self.update_binary_async_setting(element_uid=message['properties']['uid'],
                                             value=bool(message['properties']['property.value.new']))

    def _binary_sync(self, message: dict):
        """ Update a binary sync setting. """
        self.update_binary_sync_setting(element_uid=message['properties']['uid'],
                                        value=bool(message['properties']['property.value.new']))

    def _binary_sensor(self, message: dict):
        """ Update a binary sensor's state. """
        if message['properties']['property.value.new'] is not None:
            self.update_binary_sensor_state(element_uid=message['properties']['uid'],
                                            value=bool(message['properties']['property.value.new']))

    def _binary_switch(self, message: dict):
        """ Update a binary switch's state. """
        if message['properties']['property.name'] == "targetState" and \
                message['properties']['property.value.new'] is not None:
            self.update_binary_switch_state(element_uid=message['properties']['uid'],
                                            value=bool(message['properties']['property.value.new']))

    def _pending_operations(self, message: dict):
        """ Update pending operation state. """
        self.update_pending_operations(element_uid=message['properties']['uid'],
                                       pending_operations=bool(message['properties'].get('property.value.new')))

    def _current_consumption(self, message: dict):
        """ Update current consumption. """
        self.update_consumption(element_uid=message['uid'],
                                consumption="current",
                                value=message['property.value.new'])

    def _device_change(self, message: dict):
        """ Call method if a new device appears or an old one disappears. """
        if not callable(self.on_device_change):
            self._logger.error("on_device_change is not set.")
            return
        if type(message['properties']['property.value.new']) == list \
           and message['properties']['uid'] == "devolo.DevicesPage":
            self.on_device_change(uids=message['properties']['property.value.new'])

    def _device_online_state(self, message: dict):
        """ Update the device's online state. """
        if message['properties']['property.name'] == "status":
            self.update_device_online_state(device_uid=message['properties']['uid'],
                                            value=message['properties']['property.value.new'])

    def _gateway_accessible(self, message: dict):
        """ Update the gateway's state. """
        if message['properties']['property.name'] == "gatewayAccessible":
            self.update_gateway_state(accessible=message['properties']['property.value.new']['accessible'],
                                      online_sync=message['properties']['property.value.new']['onlineSync'])

    def _general_device(self, message: dict):
        """ Update general device settings. """
        self.update_general_device_settings(element_uid=message['properties']['uid'],
                                            events_enabled=message['properties']['property.value.new']['eventsEnabled'],
                                            icon=message['properties']['property.value.new']['icon'],
                                            name=message['properties']['property.value.new']['name'],
                                            zone_id=message['properties']['property.value.new']['zoneID'])

    def _grouping(self, message: dict):
        """ Update zone (also called room) of a device. """
        self._gateway.zones = {key["id"]: key["name"] for key in message["properties"]["property.value.new"]}
        self._logger.debug("Updating gateway zones.")

    def _humidity_bar(self, message: dict):
        """ Update a humidity bar. """
        fake_element_uid = f"devolo.HumidityBar:{message['properties']['uid'].split(':', 1)[1]}"
        if message['properties']['uid'].startswith("devolo.HumidityBarZone"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     zone=message['properties']['property.value.new'])
        elif message['properties']['uid'].startswith("devolo.HumidityBarValue"):
            self.update_humidity_bar(element_uid=fake_element_uid,
                                     value=message['properties']['property.value.new'])

    def _led(self, message: dict):
        """ Update LED settings. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            self.update_led(element_uid=message['properties']['uid'],
                            value=message['properties']['property.value.new'])

    def _meter(self, message: dict):
        """ Update a meter value. """
        property_name = {"currentValue": self._current_consumption,
                         "totalValue": self._total_consumption,
                         "sinceTime": self._since_time}

        property_name[message['properties']['property.name']](message['properties'])

    def _multi_level_sensor(self, message: dict):
        """ Update a multi level sensor. """
        self.update_multi_level_sensor(element_uid=message['properties']['uid'],
                                       value=message['properties']['property.value.new'])

    def _multi_level_switch(self, message: dict):
        """ Update a multi level switch. """
        if not isinstance(message['properties']['property.value.new'], (list, dict, type(None))) \
                or "smartGroup" not in message["properties"]["uid"]:
            self.update_multi_level_switch(element_uid=message['properties']['uid'],
                                           value=message['properties']['property.value.new'])

    def _multilevel_sync(self, message: dict):
        """ Update multilevel sync settings. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            self.update_multilevel_sync(element_uid=message['properties']['uid'],
                                        value=message['properties']['property.value.new'])

    def _parameter(self, message: dict):
        """ Update parameter settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            self.update_parameter(element_uid=message['properties']['uid'],
                                  param_changed=message['properties']['property.value.new'])

    def _protection(self, message: dict):
        """ Update protection settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            self.update_protection(element_uid=message['properties']['uid'],
                                   name=message['properties']['property.name'],
                                   value=message['properties']['property.value.new'])

    def _remote_control(self, message: dict):
        """ Update a remote control. """
        self.update_remote_control(element_uid=message['properties']['uid'],
                                   key_pressed=message['properties']['property.value.new'])

    def _since_time(self, message: dict):
        """ Update point in time the total consumption was reset. """
        self.update_total_since(element_uid=message['uid'],
                                total_since=message['property.value.new'])

    def _switch_type(self, message: dict):
        """ Update switch type setting (sts). """
        self.update_switch_type(element_uid=message["properties"]["uid"],
                                value=message["properties"]["property.value.new"] * 2)

    def _temperature(self, message: dict):
        """ Update temperature report settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            self.update_temperature(element_uid=message['properties']['uid'],
                                    value=message['properties']['property.value.new'])

    def _total_consumption(self, message: dict):
        """ Update total consumption. """
        self.update_consumption(element_uid=message['uid'],
                                consumption="total",
                                value=message['property.value.new'])

    def _unknown(self, message: dict):
        """ Ignore unknown messages. """
        ignore = ("devolo.DeviceEvents", "devolo.LastActivity", "ss", "mcs")
        if not message["properties"]["uid"].startswith(ignore):
            self._logger.debug(json.dumps(message, indent=4))

    def _voltage_multi_level_sensor(self, message: dict):
        """ Update a voltage value. """
        self.update_voltage(element_uid=message['properties']['uid'],
                            value=message['properties']['property.value.new'])
