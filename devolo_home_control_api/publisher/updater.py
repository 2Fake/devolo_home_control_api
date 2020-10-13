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
                        "devolo.ValveTemperatureSensor": self._multi_level_sensor,
                        "devolo.VoltageMultiLevelSensor": self._multi_level_sensor,
                        "devolo.WarningBinaryFI:": self._binary_sensor,
                        "hdm": self._device_state}

        if "property.name" in message["properties"] \
                and message['properties']['property.name'] == "pendingOperations" \
                and "smartGroup" not in message["properties"]["uid"]:
            self._pending_operations(message)
        elif "property.name" in message["properties"] \
                and message['properties']['property.name'] == "operationStatus":
            pass
        else:
            message_type.get(get_device_type_from_element_uid(message['properties']['uid']), self._unknown)(message)


    def _automatic_calibration(self, message: dict):
        """ Update a automatic calibration message. """
        try:
            calibration_status = message["properties"]["property.value.new"]["status"]
            self._update_automatic_calibration(
                element_uid=message["properties"]["uid"],
                calibration_status=calibration_status != 2,
            )
        except (KeyError, TypeError):
            if type(message["properties"]["property.value.new"]) not in [dict, list]:
                self._update_automatic_calibration(element_uid=message["properties"]["uid"],
                                                   calibration_status=bool(message["properties"]["property.value.new"]))

    def _binary_async(self, message: dict):
        """ Update a binary async setting. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            element_uid = message['properties']['uid']
            value = bool(message['properties']['property.value.new'])
            device_uid = get_device_uid_from_setting_uid(element_uid)
            try:
                self.devices[device_uid].settings_property[camel_case_to_snake_case(element_uid).split("#")[-1]].value = value
            except KeyError:
                # Siren setting is not initialized like others.
                self.devices[device_uid].settings_property['muted'].value = value
            self._logger.debug(f"Updating value of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_sync(self, message: dict):
        """ Update a binary sync setting. """
        element_uid = message['properties']['uid']
        value = bool(message['properties']['property.value.new'])
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["movement_direction"].direction = value
        self._logger.debug(f"Updating value of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_sensor(self, message: dict):
        """ Update a binary sensor's state. """
        if message['properties']['property.value.new'] is not None:
            element_uid = message['properties']['uid']
            value = bool(message['properties']['property.value.new'])
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].binary_sensor_property[element_uid].state = value
            self._logger.debug(f"Updating state of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_switch(self, message: dict):
        """ Update a binary switch's state. """
        if message['properties']['property.name'] == "targetState" and \
                message['properties']['property.value.new'] is not None and \
                "smartGroup" not in message["properties"]["uid"]:
            element_uid = message['properties']['uid']
            value = bool(message['properties']['property.value.new'])
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].binary_switch_property[element_uid].state = value
            self._logger.debug(f"Updating state of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _pending_operations(self, message: dict):
        """ Update pending operation state. """
        element_uid = message['properties']['uid']

        # Early return on useless messages
        if element_uid == "devolo.PairDevice":
            return

        pending_operations = bool(message['properties'].get('property.value.new'))
        try:
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].pending_operations = pending_operations
        except KeyError:
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].pending_operations = pending_operations
        self._logger.debug(f"Updating pending operations of device {device_uid} to {pending_operations}")
        self._publisher.dispatch(device_uid, ("pending_operations", pending_operations))

    def _current_consumption(self, message: dict):
        """ Update current consumption. """
        self._update_consumption(element_uid=message['uid'],
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

    def _device_state(self, message: dict):
        """ Update the device state. """
        propery_name = {"batteryLevel": "battery_level",
                        "batteryLow": "battery_low",
                        "status": "status"}
        
        name = message['properties']['property.name']
        device_uid = message['properties']['uid']
        value = message['properties']['property.value.new']
        try:
            self._logger.debug(f"Updating {propery_name[name]} of {device_uid} to {value}")
            setattr(self.devices[device_uid], propery_name[name], value)
            self._publisher.dispatch(device_uid, (device_uid, value, propery_name[name]))
        except KeyError:
            self._unknown(message)

    def _gateway_accessible(self, message: dict):
        """ Update the gateway's state. """
        if message['properties']['property.name'] == "gatewayAccessible":
            accessible = message['properties']['property.value.new']['accessible']
            online_sync = message['properties']['property.value.new']['onlineSync']
            self._logger.debug(f"Updating status and state of gateway to status: {accessible} and state: {online_sync}")
            self._gateway.online = accessible
            self._gateway.sync = online_sync

    def _general_device(self, message: dict):
        """ Update general device settings. """
        self._update_general_device_settings(element_uid=message['properties']['uid'],
                                             events_enabled=message['properties']['property.value.new']['eventsEnabled'],
                                             icon=message['properties']['property.value.new']['icon'],
                                             name=message['properties']['property.value.new']['name'],
                                             zone_id=message['properties']['property.value.new']['zoneID'])

    def _grouping(self, message: dict):
        """ Update zone (also called room) of a device. """
        self._gateway.zones = {key["id"]: key["name"] for key in message["properties"]["property.value.new"]}
        self._logger.debug("Updating gateway zones.")

    def _gui_enabled(self, message: dict):
        """ Update protection setting of binary switches. """
        device_uid = get_device_uid_from_element_uid(message['uid'])
        enabled = message['property.value.new']
        for element_uid in self.devices[device_uid].binary_switch_property:
            self.devices[device_uid].binary_switch_property[element_uid].enabled = enabled
            self._logger.debug(f"Updating enabled state of {element_uid} to {enabled}")
            self._publisher.dispatch(device_uid, (element_uid, enabled, "gui_enabled"))

    def _humidity_bar(self, message: dict):
        """ Update a humidity bar. """
        fake_element_uid = f"devolo.HumidityBar:{message['properties']['uid'].split(':', 1)[1]}"
        value = message['properties']['property.value.new']
        device_uid = get_device_uid_from_element_uid(fake_element_uid)
        if message['properties']['uid'].startswith("devolo.HumidityBarZone"):
            self.devices[device_uid].humidity_bar_property[fake_element_uid].zone = value
            self._logger.debug(f"Updating humidity bar zone of {fake_element_uid} to {value}")
        elif message['properties']['uid'].startswith("devolo.HumidityBarValue"):
            self.devices[device_uid].humidity_bar_property[fake_element_uid].value = value
            self._logger.debug(f"Updating humidity bar value of {fake_element_uid} to {value}")
        self._publisher.dispatch(device_uid, (fake_element_uid,
                                              self.devices[device_uid].humidity_bar_property[fake_element_uid].zone,
                                              self.devices[device_uid].humidity_bar_property[fake_element_uid].value))

    def _led(self, message: dict):
        """ Update LED settings. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            element_uid = message['properties']['uid']
            value = message['properties']['property.value.new']
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self._logger.debug(f"Updating {element_uid} to {value}.")
            self.devices[device_uid].settings_property['led'].led_setting = value
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _meter(self, message: dict):
        """ Update a meter value. """
        property_name = {"currentValue": self._current_consumption,
                         "totalValue": self._total_consumption,
                         "sinceTime": self._since_time,
                         "guiEnabled": self._gui_enabled}

        property_name[message['properties']['property.name']](message['properties'])

    def _multi_level_sensor(self, message: dict):
        """ Update a multi level sensor. """
        element_uid = message['properties']['uid']
        value = message['properties']['property.value.new']
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug(f"Updating {element_uid} to {value}")
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _multi_level_switch(self, message: dict):
        """ Update a multi level switch. """
        if not isinstance(message['properties']['property.value.new'], (list, dict, type(None))) \
                or "smartGroup" not in message['properties']['uid']:
            element_uid = message['properties']['uid']
            value = message['properties']['property.value.new']
            device_uid = get_device_uid_from_element_uid(element_uid)
            self._logger.debug(f"Updating {element_uid} to {value}")
            self.devices[device_uid].multi_level_switch_property[element_uid].value = value
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _multilevel_sync(self, message: dict):
        """ Update multilevel sync settings. """
        if type(message['properties']['property.value.new']) not in [dict, list]:
            element_uid = message['properties']['uid']
            value = message['properties']['property.value.new']
            device_uid = get_device_uid_from_setting_uid(element_uid)
            device_model = self.devices[device_uid].device_model_uid
            self._logger.debug(f"Updating {element_uid} to {value}")
            sync_type = {"devolo.model.Siren": "tone",
                         "devolo.model.OldShutter": "shutter_duration",
                         "devolo.model.Shutter": "shutter_duration"}

            try:
                setattr(self.devices[device_uid].settings_property[sync_type[device_model]], sync_type[device_model], value)
            except KeyError:
                # Other devices are up to now always motion sensors.
                self.devices[device_uid].settings_property['motion_sensitivity'].motion_sensitivity = value

            self._publisher.dispatch(device_uid, (element_uid, value))

    def _parameter(self, message: dict):
        """ Update parameter settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            element_uid = message['properties']['uid']
            param_changed = message['properties']['property.value.new']
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].settings_property['param_changed'].param_changed = param_changed
            self._logger.debug(f"Updating param_changed of {element_uid} to {param_changed}")
            self._publisher.dispatch(device_uid, (element_uid, param_changed))

    def _protection(self, message: dict):
        """ Update protection settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            element_uid = message['properties']['uid']
            value = message['properties']['property.value.new']
            name = message['properties']['property.name']
            device_uid = get_device_uid_from_setting_uid(element_uid)
            switching_type = {"targetLocalSwitch": "local_switching",
                              "localSwitch": "local_switching",
                              "targetRemoteSwitch": "remote_switching",
                              "remoteSwitch": "remote_switching"}

            setattr(self.devices[device_uid].settings_property['protection'], switching_type[name], value)
            self._logger.debug(f"Updating {switching_type[name]} protection of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value, switching_type[name]))

    def _remote_control(self, message: dict):
        """ Update a remote control. """
        element_uid = message['properties']['uid']
        key_pressed = message['properties']['property.value.new']

        # The message for the diary needs to be ignored
        if key_pressed is not None:
            device_uid = get_device_uid_from_element_uid(element_uid)
            old_key_pressed = self.devices[device_uid].remote_control_property[element_uid].key_pressed
            self.devices[device_uid].remote_control_property[element_uid].key_pressed = key_pressed
            self._logger.debug(f"Updating remote control of {element_uid}.\
                               Key {f'pressed: {key_pressed}' if key_pressed != 0 else f'released: {old_key_pressed}'}")
            self._publisher.dispatch(device_uid, (element_uid, key_pressed))

    def _since_time(self, message: dict):
        """ Update point in time the total consumption was reset. """
        element_uid = message['uid']
        total_since = message['property.value.new']
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].consumption_property[element_uid].total_since = total_since
        self._logger.debug(f"Updating total since of {element_uid} to {total_since}")
        self._publisher.dispatch(device_uid, (element_uid, total_since, "total_since"))

    def _switch_type(self, message: dict):
        """ Update switch type setting (sts). """
        element_uid = message['properties']['uid']
        value = message['properties']['property.value.new'] * 2  # FWR, value.new is 1 for 2 buttons and 2 for 4 buttons.
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property['switch_type'].value = value
        self.devices[device_uid].remote_control_property[f'devolo.RemoteControl:{device_uid}'].key_count = value
        self._logger.debug(f"Updating switch type of {device_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _temperature(self, message: dict):
        """ Update temperature report settings. """
        if type(message['properties'].get("property.value.new")) not in [dict, list]:
            element_uid = message['properties']['uid']
            value = message['properties']['property.value.new']
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].settings_property['temperature_report'].temp_report = value
            self._logger.debug(f"Updating temperature report of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _total_consumption(self, message: dict):
        """ Update total consumption. """
        self._update_consumption(element_uid=message['uid'],
                                 consumption="total",
                                 value=message['property.value.new'])

    def _unknown(self, message: dict):
        """ Ignore unknown messages. """
        ignore = ("devolo.DeviceEvents",
                  "devolo.LastActivity",
                  "devolo.PairDevice",
                  "devolo.mprm.gw.GatewayManager",
                  "devolo.mprm.gw.PortalManager",
                  "devolo.smartGroup",
                  "ss",
                  "mcs")
        if not message["properties"]["uid"].startswith(ignore):
            self._logger.debug(json.dumps(message, indent=4))

    def _update_automatic_calibration(self, element_uid: str, calibration_status: bool):
        """ Update automatic calibration setting of a device. """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["automatic_calibration"].calibration_status = calibration_status
        self._logger.debug(f"Updating value of {element_uid} to {calibration_status}")
        self._publisher.dispatch(device_uid, (element_uid, calibration_status))

    def _update_consumption(self, element_uid: str, consumption: str, value: float):
        """ Update the consumption of a device. """
        device_uid = get_device_uid_from_element_uid(element_uid)
        setattr(self.devices[device_uid].consumption_property[element_uid], consumption, value)
        self._logger.debug(f"Updating {consumption} consumption of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value, consumption))

    def _update_general_device_settings(self, element_uid, **kwargs: str):
        """ Update general device settings. """
        device_uid = get_device_uid_from_setting_uid(element_uid)
        for key, value in kwargs.items():
            setattr(self.devices[device_uid].settings_property['general_device_settings'], key, value)
            self._logger.debug(f"Updating attribute: {key} of {element_uid} to {value}")
            self._publisher.dispatch(device_uid, (key, value))

    def _voltage_multi_level_sensor(self, message: dict):
        """ Update a voltage value. """
        element_uid = message['properties']['uid']
        value = message['properties']['property.value.new']
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._logger.debug(f"Updating voltage of {element_uid} to {value}")
        self._publisher.dispatch(device_uid, (element_uid, value))
