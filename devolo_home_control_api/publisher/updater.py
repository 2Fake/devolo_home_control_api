"""The Updater"""
import json
import logging
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..backend import MESSAGE_TYPES
from ..devices.gateway import Gateway
from ..devices.zwave import Zwave
from ..helper.string import camel_case_to_snake_case
from ..helper.uid import get_device_type_from_element_uid, get_device_uid_from_element_uid, get_device_uid_from_setting_uid
from .publisher import Publisher


class Updater:  # pylint: disable=too-few-public-methods
    """
    The Updater takes care of new states and values of devices and sends them to the Publisher object. Using methods in here
    do not effect the real device states.

    :param devices: List of devices to await updates for
    :param gateway: Instance of a Gateway object
    :param publisher: Instance of a Publisher object
    """

    def __init__(self, devices: Dict[str, Zwave], gateway: Gateway, publisher: Publisher) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = gateway
        self._publisher = publisher

        self.devices = devices
        self.on_device_change: Optional[Callable[[List[str]], Tuple[str, str]]] = None

    def update(self, message: Dict[str, Any]) -> None:
        """
        Update states and values depending on the message type.

        :param message: Message to process
        """
        unwanted_properties = [
            ".unregistering",
            "assistantsConnected",
            "operationStatus",
        ]

        # Early return on unwanted messages
        if (
            "UNREGISTERED" in message["topic"]
            or message["properties"]["property.name"] in unwanted_properties
            or "smartGroup" in message["properties"]["uid"]
        ):
            return

        # Handle pending operations messages
        if "property.name" in message["properties"] and message["properties"]["property.name"] == "pendingOperations":
            self._pending_operations(message)
            return

        # Handle all other messages
        message_type = MESSAGE_TYPES.get(get_device_type_from_element_uid(message["properties"]["uid"]), "_unknown")
        with suppress(AttributeError, KeyError):  # Sometime we receive already messages although the device is not setup yet.
            getattr(self, message_type)(message)

    def _automatic_calibration(self, message: Dict[str, Any]) -> None:
        """Update a automatic calibration message."""
        try:
            calibration_status = message["properties"]["property.value.new"]["status"]
            self._update_automatic_calibration(
                element_uid=message["properties"]["uid"], calibration_status=calibration_status != 2
            )
        except (KeyError, TypeError):
            if type(message["properties"]["property.value.new"]) not in [dict, list]:
                self._update_automatic_calibration(
                    element_uid=message["properties"]["uid"],
                    calibration_status=bool(message["properties"]["property.value.new"]),
                )

    def _binary_async(self, message: Dict[str, Any]) -> None:
        """Update a binary async setting."""
        if type(message["properties"]["property.value.new"]) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            value = bool(message["properties"]["property.value.new"])
            device_uid = get_device_uid_from_setting_uid(element_uid)
            try:
                self.devices[device_uid].settings_property[camel_case_to_snake_case(element_uid).split("#")[-1]].value = value
            except KeyError:
                # Siren setting is not initialized like others.
                self.devices[device_uid].settings_property["muted"].value = value
            self._logger.debug("Updating state of %s to %s", element_uid, value)
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_sync(self, message: Dict[str, Any]) -> None:
        """Update a binary sync setting."""
        element_uid: str = message["properties"]["uid"]
        value = bool(message["properties"]["property.value.new"])
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["movement_direction"].direction = value
        self._logger.debug("Updating state of %s to %s", element_uid, value)
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_sensor(self, message: Dict[str, Any]) -> None:
        """Update a binary sensor's state."""
        if message["properties"]["property.value.new"] is not None:
            element_uid: str = message["properties"]["uid"]
            value = bool(message["properties"]["property.value.new"])
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].binary_sensor_property[element_uid].state = value
            self._logger.debug("Updating state of %s to %s", element_uid, value)
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _binary_switch(self, message: Dict[str, Any]) -> None:
        """Update a binary switch's state."""
        if message["properties"]["property.name"] == "targetState" and message["properties"]["property.value.new"] is not None:
            element_uid: str = message["properties"]["uid"]
            value = bool(message["properties"]["property.value.new"])
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].binary_switch_property[element_uid].state = value
            self._logger.debug("Updating state of %s to %s", element_uid, value)
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _pending_operations(self, message: Dict[str, Any]) -> None:
        """Update pending operation state."""
        element_uid: str = message["properties"]["uid"]

        # Early return on useless messages
        if [
            uid
            for uid in ["devolo.HttpRequest", "devolo.PairDevice", "devolo.RemoveDevice", "devolo.mprm.gw.GatewayManager"]
            if (uid in element_uid)
        ]:
            return

        pending_operations = bool(message["properties"].get("property.value.new"))
        try:
            device_uid = get_device_uid_from_element_uid(element_uid)
            self.devices[device_uid].pending_operations = pending_operations
        except KeyError:
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].pending_operations = pending_operations
        self._logger.debug("Updating pending operations of device %s to %s", device_uid, pending_operations)
        self._publisher.dispatch(device_uid, ("pending_operations", pending_operations))

    def _current_consumption(self, message: Dict[str, Any]) -> None:
        """Update current consumption."""
        self._update_consumption(element_uid=message["uid"], consumption="current", value=message["property.value.new"])

    def _device_state(self, message: Dict[str, Any]) -> None:
        """Update the device state."""
        property_name = {
            "batteryLevel": "battery_level",
            "batteryLow": "battery_low",
            "status": "status",
        }

        device_uid = message["properties"]["uid"]
        name = message["properties"]["property.name"]
        value = message["properties"]["property.value.new"]

        try:
            self._logger.debug("Updating %s of %s to %s", property_name[name], device_uid, value)
            setattr(self.devices[device_uid], property_name[name], value)
            self._publisher.dispatch(device_uid, (device_uid, value, property_name[name]))
        except KeyError:
            self._unknown(message)

    def _gateway_accessible(self, message: Dict[str, Any]) -> None:
        """Update the gateway's state."""
        if message["properties"]["property.name"] == "gatewayAccessible":
            accessible = message["properties"]["property.value.new"]["accessible"]
            online_sync = message["properties"]["property.value.new"]["onlineSync"]
            self._logger.debug("Updating status and state of gateway to status: %s and state: %s", accessible, online_sync)
            self._gateway.online = accessible
            self._gateway.sync = online_sync

    def _general_device(self, message: Dict[str, Any]) -> None:
        """Update general device settings."""
        self._update_general_device_settings(
            element_uid=message["properties"]["uid"],
            events_enabled=message["properties"]["property.value.new"]["eventsEnabled"],
            icon=message["properties"]["property.value.new"]["icon"],
            name=message["properties"]["property.value.new"]["name"],
            zone_id=message["properties"]["property.value.new"]["zoneID"],
            zones=self._gateway.zones,
        )

    def _grouping(self, message: Dict[str, Any]) -> None:
        """Update zone (also called room) of a device."""
        self._gateway.zones = {key["id"]: key["name"] for key in message["properties"]["property.value.new"]}
        self._logger.debug("Updating gateway zones.")

    def _gui_enabled(self, message: Dict[str, Any]) -> None:
        """Update protection setting of binary switches."""
        device_uid = get_device_uid_from_element_uid(message["uid"])
        enabled = message["property.value.new"]
        for element_uid in self.devices[device_uid].binary_switch_property:
            self.devices[device_uid].binary_switch_property[element_uid].enabled = enabled
            self._logger.debug("Updating enabled state of %s to %s", element_uid, enabled)
            self._publisher.dispatch(device_uid, (element_uid, enabled, "gui_enabled"))

    def _humidity_bar(self, message: Dict[str, Any]) -> None:
        """Update a humidity bar."""
        fake_element_uid = f"devolo.HumidityBar:{message['properties']['uid'].split(':', 1)[1]}"
        value = message["properties"]["property.value.new"]
        device_uid = get_device_uid_from_element_uid(fake_element_uid)
        if message["properties"]["uid"].startswith("devolo.HumidityBarZone"):
            self.devices[device_uid].humidity_bar_property[fake_element_uid].zone = value
            self._logger.debug("Updating humidity bar zone of %s to %s", fake_element_uid, value)
        elif message["properties"]["uid"].startswith("devolo.HumidityBarValue"):
            self.devices[device_uid].humidity_bar_property[fake_element_uid].value = value
            self._logger.debug("Updating humidity bar value of %s to %s", fake_element_uid, value)
        self._publisher.dispatch(
            device_uid,
            (
                fake_element_uid,
                self.devices[device_uid].humidity_bar_property[fake_element_uid].zone,
                self.devices[device_uid].humidity_bar_property[fake_element_uid].value,
            ),
        )

    def _inspect_devices(self, message: Dict[str, Any]) -> None:
        """Call method if a new device appears or an old one disappears."""
        if not callable(self.on_device_change):
            self._logger.error("on_device_change is not set.")
            return

        if (
            not isinstance(message["properties"]["property.value.new"], list)
            or message["properties"]["uid"] != "devolo.DevicesPage"
        ):
            return

        device_uid, mode = self.on_device_change(message["properties"]["property.value.new"])
        if mode == "add":
            self._logger.info("%s added.", device_uid)
            self._publisher.add_event(event=device_uid)
            self._publisher.dispatch(device_uid, (device_uid, mode))
        else:
            self._publisher.dispatch(device_uid, (device_uid, mode))
            self._publisher.delete_event(event=device_uid)

    def _led(self, message: Dict[str, Any]) -> None:
        """Update LED settings."""
        if type(message["properties"]["property.value.new"]) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            value = message["properties"]["property.value.new"]
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self._logger.debug("Updating %s to %s.", element_uid, value)
            self.devices[device_uid].settings_property["led"].led_setting = value
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _meter(self, message: Dict[str, Any]) -> None:
        """Update a meter value."""
        property_name = {
            "currentValue": self._current_consumption,
            "totalValue": self._total_consumption,
            "sinceTime": self._since_time,
            "guiEnabled": self._gui_enabled,
        }

        property_name[message["properties"]["property.name"]](message["properties"])

    def _multilevel_async(self, message: Dict[str, Any]) -> None:
        """Update multilevel async setting (mas) properties."""
        device_uid = get_device_uid_from_setting_uid(message["properties"]["uid"])
        try:
            name = camel_case_to_snake_case(message["properties"]["itemId"])
        # The Metering Plug has an multilevel async setting without an ID
        except KeyError:
            if self.devices[device_uid].device_model_uid == "devolo.model.Wall:Plug:Switch:and:Meter":
                name = "flash_mode"
            else:
                raise
        self.devices[device_uid].settings_property[name].value = message["properties"]["property.value.new"]

    def _multi_level_sensor(self, message: Dict[str, Any]) -> None:
        """Update a multi level sensor."""
        element_uid: str = message["properties"]["uid"]
        value = message["properties"]["property.value.new"]
        device_uid = get_device_uid_from_element_uid(element_uid)
        self._logger.debug("Updating %s to %s.", element_uid, value)
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _multi_level_switch(self, message: Dict[str, Any]) -> None:
        """Update a multi level switch."""
        if not isinstance(message["properties"]["property.value.new"], (list, dict, type(None))):
            element_uid: str = message["properties"]["uid"]
            value = message["properties"]["property.value.new"]
            device_uid = get_device_uid_from_element_uid(element_uid)
            self._logger.debug("Updating %s to %s.", element_uid, value)
            self.devices[device_uid].multi_level_switch_property[element_uid].value = value
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _multilevel_sync(self, message: Dict[str, Any]) -> None:
        """Update multilevel sync settings."""
        if type(message["properties"]["property.value.new"]) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            value = message["properties"]["property.value.new"]
            device_uid = get_device_uid_from_setting_uid(element_uid)
            device_model = self.devices[device_uid].device_model_uid
            self._logger.debug("Updating %s to %s.", element_uid, value)
            sync_type = {
                "devolo.model.Siren": "tone",
                "devolo.model.OldShutter": "shutter_duration",
                "devolo.model.Shutter": "shutter_duration",
            }

            try:
                setattr(self.devices[device_uid].settings_property[sync_type[device_model]], sync_type[device_model], value)
            except KeyError:
                # Other devices are up to now always motion sensors.
                self.devices[device_uid].settings_property["motion_sensitivity"].motion_sensitivity = value

            self._publisher.dispatch(device_uid, (element_uid, value))

    def _parameter(self, message: Dict[str, Any]) -> None:
        """Update parameter settings."""
        if type(message["properties"].get("property.value.new")) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            param_changed = message["properties"]["property.value.new"]
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].settings_property["param_changed"].param_changed = param_changed
            self._logger.debug("Updating %s to %s.", element_uid, param_changed)
            self._publisher.dispatch(device_uid, (element_uid, param_changed))

    def _protection(self, message: Dict[str, Any]) -> None:
        """Update protection settings."""
        if type(message["properties"].get("property.value.new")) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            value = message["properties"]["property.value.new"]
            name = message["properties"]["property.name"]
            device_uid = get_device_uid_from_setting_uid(element_uid)
            switching_type = {
                "targetLocalSwitch": "local_switching",
                "localSwitch": "local_switching",
                "targetRemoteSwitch": "remote_switching",
                "remoteSwitch": "remote_switching",
            }

            setattr(self.devices[device_uid].settings_property["protection"], switching_type[name], value)
            self._logger.debug("Updating %s protection of %s to %s", switching_type[name], element_uid, value)
            self._publisher.dispatch(device_uid, (element_uid, value, switching_type[name]))

    def _remote_control(self, message: Dict[str, Any]) -> None:
        """Update a remote control."""
        element_uid: str = message["properties"]["uid"]
        key_pressed = message["properties"]["property.value.new"]

        # The message for the diary needs to be ignored
        if key_pressed is not None:
            device_uid = get_device_uid_from_element_uid(element_uid)
            old_key_pressed = self.devices[device_uid].remote_control_property[element_uid].key_pressed
            self.devices[device_uid].remote_control_property[element_uid].key_pressed = key_pressed
            self._logger.debug(
                "Updating remote control of %s. Key %s",
                element_uid,
                f"pressed: {key_pressed}" if key_pressed != 0 else f"released: {old_key_pressed}",
            )
            self._publisher.dispatch(device_uid, (element_uid, key_pressed))

    def _since_time(self, message: Dict[str, Any]) -> None:
        """Update point in time the total consumption was reset."""
        element_uid = message["uid"]
        total_since = message["property.value.new"]
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].consumption_property[element_uid].total_since = total_since
        self._logger.debug("Updating total since of %s to %s", element_uid, total_since)
        self._publisher.dispatch(device_uid, (element_uid, total_since, "total_since"))

    def _switch_type(self, message: Dict[str, Any]) -> None:
        """Update switch type setting (sts)."""
        element_uid: str = message["properties"]["uid"]
        value = message["properties"]["property.value.new"] * 2  # FWR, value.new is 1 for 2 buttons and 2 for 4 buttons.
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["switch_type"].value = value
        self.devices[device_uid].remote_control_property[f"devolo.RemoteControl:{device_uid}"].key_count = value
        self._logger.debug("Updating switch type of %s to %s", device_uid, value)
        self._publisher.dispatch(device_uid, (element_uid, value))

    def _temperature_report(self, message: Dict[str, Any]) -> None:
        """Update temperature report settings."""
        if type(message["properties"].get("property.value.new")) not in [dict, list]:
            element_uid: str = message["properties"]["uid"]
            value = message["properties"]["property.value.new"]
            device_uid = get_device_uid_from_setting_uid(element_uid)
            self.devices[device_uid].settings_property["temperature_report"].temp_report = value
            self._logger.debug("Updating temperature report of %s to %s", element_uid, value)
            self._publisher.dispatch(device_uid, (element_uid, value))

    def _total_consumption(self, message: Dict[str, Any]) -> None:
        """Update total consumption."""
        self._update_consumption(element_uid=message["uid"], consumption="total", value=message["property.value.new"])

    def _unknown(self, message: Dict[str, Any]) -> None:
        """Ignore unknown messages."""
        ignore = (
            "devolo.DeviceEvents",
            "devolo.PairDevice",
            "devolo.SirenBinarySensor",
            "devolo.SirenMultiLevelSensor",
            "devolo.mprm.gw.GatewayManager",
            "devolo.mprm.gw.PortalManager",
            "ss",
            "mcs",
        )
        if not message["properties"]["uid"].startswith(ignore):
            self._logger.debug(json.dumps(message, indent=4))

    def _update_automatic_calibration(self, element_uid: str, calibration_status: bool) -> None:
        """Update automatic calibration setting of a device."""
        device_uid = get_device_uid_from_setting_uid(element_uid)
        self.devices[device_uid].settings_property["automatic_calibration"].calibration_status = calibration_status
        self._logger.debug("Updating value of %s to %s", element_uid, calibration_status)
        self._publisher.dispatch(device_uid, (element_uid, calibration_status))

    def _update_consumption(self, element_uid: str, consumption: str, value: float) -> None:
        """Update the consumption of a device."""
        device_uid = get_device_uid_from_element_uid(element_uid)
        setattr(self.devices[device_uid].consumption_property[element_uid], consumption, value)
        self._logger.debug("Updating %s consumption of %s to %s", consumption, element_uid, value)
        self._publisher.dispatch(device_uid, (element_uid, value, consumption))

    def _update_general_device_settings(self, element_uid: str, **kwargs: Any) -> None:
        """Update general device settings."""
        device_uid = get_device_uid_from_setting_uid(element_uid)
        for key, value in kwargs.items():
            setattr(self.devices[device_uid].settings_property["general_device_settings"], key, value)
            self._logger.debug("Updating attribute: %s of %s to %s", key, element_uid, value)
            self._publisher.dispatch(device_uid, (key, value))

    def _voltage_multi_level_sensor(self, message: Dict[str, Any]) -> None:
        """Update a voltage value."""
        element_uid: str = message["properties"]["uid"]
        value = message["properties"]["property.value.new"]
        device_uid = get_device_uid_from_element_uid(element_uid)
        self.devices[device_uid].multi_level_sensor_property[element_uid].value = value
        self._logger.debug("Updating voltage of %s to %s", element_uid, value)
        self._publisher.dispatch(device_uid, (element_uid, value))
