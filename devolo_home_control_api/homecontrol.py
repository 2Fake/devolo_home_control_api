import threading
from typing import Optional

import requests
from zeroconf import Zeroconf

from . import __version__
from .backend.mprm import Mprm
from .devices.gateway import Gateway
from .devices.zwave import Zwave
from .helper.string import camel_case_to_snake_case
from .helper.uid import (get_device_type_from_element_uid,
                         get_device_uid_from_element_uid,
                         get_device_uid_from_setting_uid)
from .properties.binary_sensor_property import BinarySensorProperty
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty
from .properties.humidity_bar_property import HumidityBarProperty
from .properties.multi_level_sensor_property import MultiLevelSensorProperty
from .properties.multi_level_switch_property import MultiLevelSwitchProperty
from .properties.remote_control_property import RemoteControlProperty
from .properties.settings_property import SettingsProperty
from .publisher.publisher import Publisher
from .publisher.updater import Updater


class HomeControl(Mprm):
    """
    Representing object for your Home Control setup. This is more or less the glue between your devolo Home Control Central
    Unit, your devices and their properties.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param zeroconf_instance: Zeroconf instance to be potentially reused
    :param url: URL of the mPRM (typically leave it at default)
    """

    def __init__(self, gateway_id: str, zeroconf_instance: Optional[Zeroconf] = None,
                 url: str = "https://homecontrol.mydevolo.com"):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": f"devolo_home_control_api/{__version__}"})
        self._session.url = url.rstrip("/")

        self.gateway = Gateway(gateway_id)
        super().__init__(zeroconf_instance)

        self.gateway.zones = self.get_all_zones()

        # Create the initial device dict
        self.devices = {}
        self._inspect_devices(self.get_all_devices())

        self.device_names = dict(zip([(self.devices[device].settings_property['general_device_settings'].name + "/"
                                       + self.devices[device].settings_property['general_device_settings'].zone)
                                      for device in self.devices],
                                     [self.devices[device].uid for device in self.devices]))

        self.publisher = Publisher([device for device in self.devices])

        self.updater = Updater(devices=self.devices, gateway=self.gateway, publisher=self.publisher)
        self.updater.on_device_change = self.device_change

        threading.Thread(target=self.websocket_connect, name=f"{__class__.__name__}.websocket_connect").start()
        self.wait_for_websocket_establishment()

    @property
    def binary_sensor_devices(self) -> list:
        """ Get all binary sensor devices. """
        return [self.devices[uid] for uid in self.devices if hasattr(self.devices[uid], "binary_sensor_property")]

    @property
    def binary_switch_devices(self) -> list:
        """ Get all binary switch devices. """
        return [self.devices[uid] for uid in self.devices if hasattr(self.devices[uid], "binary_switch_property")]

    @property
    def blinds_devices(self) -> list:
        """ Get all blinds devices. """
        blinds_devices = []
        for device in self.multi_level_switch_devices:
            blinds_devices.extend([self.devices[device.uid] for multi_level_switch_property
                                   in device.multi_level_switch_property
                                   if multi_level_switch_property.startswith("devolo.Blinds")])
        return blinds_devices

    @property
    def multi_level_sensor_devices(self) -> list:
        """ Get all multi level sensor devices. """
        return [self.devices[uid] for uid in self.devices if hasattr(self.devices[uid], "multi_level_sensor_property")]

    @property
    def multi_level_switch_devices(self) -> list:
        """ Get all multi level switch devices. This also includes blinds devices. """
        return [self.devices[uid] for uid in self.devices if hasattr(self.devices[uid], "multi_level_switch_property")]

    @property
    def remote_control_devices(self) -> list:
        """ Get all remote control devices. """
        return [self.devices[uid] for uid in self.devices if hasattr(self.devices[uid], "remote_control_property")]

    def device_change(self, device_uids: list):
        """
        React on new devices or removed devices. As the Z-Wave controller can only be in inclusion or exclusion mode, we
        assume, that you cannot add and remove devices at the same time. So if the number of devices increases, there is
        a new one and if the number decreases, a device was removed.

        :param device_uids: List of UIDs known by the backend
        """
        if len(device_uids) > len(self.devices):
            new_device = [device for device in device_uids if device not in self.devices]
            self._logger.debug(f"New device found {new_device}")
            self._inspect_devices([new_device[0]])
            self.publisher = Publisher([device for device in self.devices])
        else:
            devices = [device for device in self.devices if device not in device_uids]
            self._logger.debug(f"Device {devices} removed")
            del self.devices[devices[0]]
        self.updater.devices = self.devices

    def on_update(self, message):
        """
        Initialize steps needed to update properties on a new message.

        :param message: Message because of which we need to update properties
        """
        self.updater.update(message)

    def _binary_sensor(self, uid_info: dict):
        """ Process BinarySensor properties"""
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        if not hasattr(self.devices[device_uid], "binary_sensor_property"):
            self.devices[device_uid].binary_sensor_property = {}
        self._logger.debug(f"Adding binary sensor property to {device_uid}.")
        self.devices[device_uid].binary_sensor_property[uid_info['UID']] = \
            BinarySensorProperty(session=self._session,
                                 gateway=self.gateway,
                                 element_uid=uid_info['UID'],
                                 state=bool(uid_info['properties']['state']),
                                 sensor_type=uid_info['properties']['sensorType'],
                                 sub_type=uid_info['properties']['subType'])

    def _binary_switch(self, uid_info: dict):
        """ Process BinarySwitch properties. """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        if not hasattr(self.devices[device_uid], "binary_switch_property"):
            self.devices[device_uid].binary_switch_property = {}
        self._logger.debug(f"Adding binary switch property to {device_uid}.")
        self.devices[device_uid].binary_switch_property[uid_info['UID']] = \
            BinarySwitchProperty(session=self._session,
                                 gateway=self.gateway,
                                 element_uid=uid_info['UID'],
                                 state=bool(uid_info['properties']['state']),
                                 enabled=uid_info['properties']['guiEnabled'])

    def _general_device(self, uid_info: dict):
        """ Process general device setting (gds) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding general device settings to {device_uid}.")
        self.devices[device_uid]. \
            settings_property['general_device_settings'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             events_enabled=uid_info['properties']['settings']['eventsEnabled'],
                             name=uid_info['properties']['settings']['name'],
                             zone_id=uid_info['properties']['settings']['zoneID'],
                             icon=uid_info['properties']['settings']['icon'])

    def _humidity_bar(self, uid_info: dict):
        """
        Process HumidityBarZone and HumidityBarValue properties.

        For whatever reason, the zone and the position within that zone are two different FIs. Nevertheless, it does not make
        sense to separate them. So we fake an FI and a sensorType to combine them together into one object.
        """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        fake_element_uid = f"devolo.HumidityBar:{uid_info['UID'].split(':', 1)[1]}"
        if not hasattr(self.devices[device_uid], "humidity_bar_property"):
            self.devices[device_uid].humidity_bar_property = {}
        if self.devices[device_uid].humidity_bar_property.get(fake_element_uid) is None:
            self.devices[device_uid].humidity_bar_property[fake_element_uid] = \
                HumidityBarProperty(session=self._session,
                                    gateway=self.gateway,
                                    element_uid=fake_element_uid,
                                    sensorType="humidityBar")
        if uid_info['properties']['sensorType'] == "humidityBarZone":
            self._logger.debug(f"Adding humidity bar zone property to {device_uid}.")
            self.devices[device_uid].humidity_bar_property[fake_element_uid].zone = uid_info['properties']['value']
        elif uid_info['properties']['sensorType'] == "humidityBarPos":
            self._logger.debug(f"Adding humidity bar position property to {device_uid}.")
            self.devices[device_uid].humidity_bar_property[fake_element_uid].value = uid_info['properties']['value']

    def _inspect_devices(self, devices: list):
        """ Inspect device properties of given list of devices. """
        devices_properties = self.get_data_from_uid_list(devices)
        for device_properties in devices_properties:
            properties = device_properties['properties']
            self.devices[device_properties['UID']] = Zwave(**properties)
            self.devices[device_properties['UID']].settings_property = {}
            threading.Thread(target=self.devices[device_properties['UID']].get_zwave_info,
                             name=f"{__class__.__name__}.{self.devices[device_properties['UID']].uid}").start()

        elements = {"devolo.BinarySensor": self._binary_sensor,
                    "devolo.BinarySwitch": self._binary_switch,
                    "devolo.Blinds": self._multi_level_switch,
                    "devolo.DewpointSensor": self._multi_level_sensor,
                    "devolo.Dimmer": self._multi_level_switch,
                    "devolo.HumidityBarValue": self._humidity_bar,
                    "devolo.HumidityBarZone": self._humidity_bar,
                    "devolo.LastActivity": self._last_activity,
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
                    "devolo.WarningBinaryFI": self._binary_sensor,
                    "acs.hdm": self._automatic_calibration,
                    "bas.hdm": self._binary_async,
                    "bss.hdm": self._binary_sync,
                    "lis.hdm": self._led,
                    "gds.hdm": self._general_device,
                    "cps.hdm": self._parameter,
                    "mas.hdm": self._multilevel_async,
                    "mss.hdm": self._multilevel_sync,
                    "ps.hdm": self._protection,
                    "sts.hdm": self._switch_type,
                    "stmss.hdm": self._multilevel_sync,
                    "trs.hdm": self._temperature_report,
                    "vfs.hdm": self._led
                    }

        # List comprehension gets the list of uids from every device
        nested_uids_lists = [(uid['properties'].get("settingUIDs")
                              + uid['properties']['elementUIDs'])
                             for uid in devices_properties]

        # List comprehension gets all uids into one list to make one big call against the mPRM
        uid_list = [uid for sublist in nested_uids_lists for uid in sublist]

        device_properties_list = self.get_data_from_uid_list(uid_list)

        for uid_info in device_properties_list:
            elements.get(get_device_type_from_element_uid(uid_info['UID']), self._unknown)(uid_info)
            try:
                uid = self.devices[get_device_uid_from_element_uid(uid_info['UID'])]
            except KeyError:
                uid = self.devices[get_device_uid_from_setting_uid(uid_info['UID'])]
            uid.pending_operations = uid.pending_operations or bool(uid_info['properties'].get("pendingOperations"))

        # Last activity messages sometimes arrive before a device was initialized and therefore need to be handled afterwards.
        [self._last_activity(uid_info) for uid_info in device_properties_list
            if uid_info['UID'].startswith("devolo.LastActivity")]

    def _automatic_calibration(self, uid_info: dict):
        """ Process automatic calibration (acs) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding automatic calibration setting to {device_uid}")
        self.devices[device_uid].settings_property['automatic_calibration'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             calibration_status=bool(uid_info['properties']['calibrationStatus']))

    def _binary_sync(self, uid_info: dict):
        """
        Process binary sync setting (bss) properties. Currently only the direction of a shutter in known to be a binary sync
        setting property, so it is named nicely.
        """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding binary sync setting to {device_uid}")
        self.devices[device_uid].settings_property['movement_direction'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             inverted=uid_info['properties']['value'])

    def _binary_async(self, uid_info: dict):
        """ Process binary async setting (bas) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding binary async settings to {device_uid}.")
        settings_property = SettingsProperty(session=self._session,
                                             gateway=self.gateway,
                                             element_uid=uid_info['UID'],
                                             value=uid_info['properties']['value'])

        # The siren needs to be handled differently, as otherwise their binary async setting will not be named nicely
        if self.devices[device_uid].device_model_uid == "devolo.model.Siren":
            self.devices[device_uid].settings_property['muted'] = settings_property
        # As some devices have multiple binary async settings, we use the settings UID split after a '#' as key
        else:
            key = camel_case_to_snake_case(uid_info['UID'].split("#")[-1])
            self.devices[device_uid].settings_property[key] = settings_property

    def _last_activity(self, uid_info: dict):
        """
        Process last activity properties. Those don't go into an own property but will be appended to a parent property.
        This parent property is found by string replacement.
        """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        parent_element_uid = uid_info['UID'].replace("LastActivity", "BinarySensor")
        try:
            self.devices[device_uid].binary_sensor_property[parent_element_uid].last_activity = \
                uid_info['properties']['lastActivityTime']
        except KeyError:
            parent_element_uid = uid_info['UID'].replace("LastActivity", "SirenBinarySensor")
            self.devices[device_uid].binary_sensor_property[parent_element_uid].last_activity = \
                uid_info['properties']['lastActivityTime']

    def _led(self, uid_info: dict):
        """ Process LED information setting (lis) and visual feedback setting (vfs) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding led settings to {device_uid}.")
        try:
            led_setting = uid_info['properties']['led']
        except KeyError:
            led_setting = uid_info['properties']['feedback']
        self.devices[device_uid].settings_property['led'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             led_setting=led_setting)

    def _meter(self, uid_info: dict):
        """ Process meter properties. """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        if not hasattr(self.devices[device_uid], "consumption_property"):
            self.devices[device_uid].consumption_property = {}
        self._logger.debug(f"Adding consumption property to {device_uid}.")
        self.devices[device_uid].consumption_property[uid_info['UID']] = \
            ConsumptionProperty(session=self._session,
                                gateway=self.gateway,
                                element_uid=uid_info['UID'],
                                current=uid_info['properties']['currentValue'],
                                total=uid_info['properties']['totalValue'],
                                total_since=uid_info['properties']['sinceTime'])

    def _multilevel_async(self, uid_info: dict):
        """ Process multilevel async setting (mas) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        try:
            name = camel_case_to_snake_case(uid_info['properties']['itemId'])
        # The Metering Plug has an multilevel async setting without an ID
        except TypeError:
            if self.devices[device_uid].device_model_uid == "devolo.model.Wall:Plug:Switch:and:Meter":
                name = "flash_mode"
            else:
                raise

        self._logger.debug(f"Adding {name} setting to {device_uid}.")
        self.devices[device_uid].settings_property[name] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             value=uid_info['properties']['value'])

    def _multilevel_sync(self, uid_info: dict):
        """ Process multilevel sync setting (mss) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])

        # The siren needs to be handled differently, as otherwise their multilevel sync setting will not be named nicely.
        if self.devices[device_uid].device_model_uid == "devolo.model.Siren":
            self._logger.debug(f"Adding tone settings to {device_uid}.")
            self.devices[device_uid].settings_property['tone'] = \
                SettingsProperty(session=self._session,
                                 gateway=self.gateway,
                                 element_uid=uid_info['UID'],
                                 tone=uid_info['properties']['value'])

        # The shutter needs to be handled differently, as otherwise their multilevel sync setting will not be named nicely.
        elif self.devices[device_uid].device_model_uid in ("devolo.model.OldShutter", "devolo.model.Shutter"):
            self._logger.debug(f"Adding shutter duration settings to {device_uid}.")
            self.devices[device_uid].settings_property['shutter_duration'] = \
                SettingsProperty(session=self._session,
                                 gateway=self.gateway,
                                 element_uid=uid_info['UID'],
                                 shutter_duration=uid_info['properties']['value'])

        # Other devices are up to now always motion sensors.
        else:
            self._logger.debug(f"Adding motion sensitivity settings to {device_uid}.")
            self.devices[device_uid].settings_property['motion_sensitivity'] = \
                SettingsProperty(session=self._session,
                                 gateway=self.gateway,
                                 element_uid=uid_info['UID'],
                                 motion_sensitivity=uid_info['properties']['value'])

    def _multi_level_sensor(self, uid_info: dict):
        """ Process multi level sensor properties. """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        if not hasattr(self.devices[device_uid], "multi_level_sensor_property"):
            self.devices[device_uid].multi_level_sensor_property = {}
        self._logger.debug(f"Adding multi level sensor property {uid_info.get('UID')} to {device_uid}.")
        self.devices[device_uid].multi_level_sensor_property[uid_info['UID']] = \
            MultiLevelSensorProperty(session=self._session,
                                     gateway=self.gateway,
                                     element_uid=uid_info['UID'],
                                     value=uid_info['properties']['value'],
                                     unit=uid_info['properties']['unit'],
                                     sensor_type=uid_info['properties']['sensorType'])

    def _multi_level_switch(self, uid_info: dict):
        """ Process multi level switch properties. """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        if not hasattr(self.devices[device_uid], "multi_level_switch_property"):
            self.devices[device_uid].multi_level_switch_property = {}
        self._logger.debug(f"Adding multi level switch property {uid_info.get('UID')} to {device_uid}.")
        self.devices[device_uid].multi_level_switch_property[uid_info['UID']] = \
            MultiLevelSwitchProperty(session=self._session,
                                     gateway=self.gateway,
                                     element_uid=uid_info['UID'],
                                     value=uid_info['properties']['value'],
                                     switch_type=uid_info['properties']['switchType'],
                                     max=uid_info['properties']['max'],
                                     min=uid_info['properties']['min'])

    def _parameter(self, uid_info: dict):
        """ Process custom parameter setting (cps) properties."""
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding parameter settings to {device_uid}.")
        self.devices[device_uid].settings_property['param_changed'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             param_changed=uid_info['properties']['paramChanged'])

    def _protection(self, uid_info: dict):
        """ Process protection setting (ps) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding protection settings to {device_uid}.")
        self.devices[device_uid].settings_property['protection'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             local_switching=uid_info['properties']['localSwitch'],
                             remote_switching=uid_info['properties']['remoteSwitch'])

    def _remote_control(self, uid_info: dict):
        """ Process remote control properties. """
        device_uid = get_device_uid_from_element_uid(uid_info['UID'])
        self._logger.debug(f"Adding remote control to {device_uid}")
        if not hasattr(self.devices[device_uid], "remote_control_property"):
            self.devices[device_uid].remote_control_property = {}
        self.devices[device_uid].remote_control_property[uid_info['UID']] = \
            RemoteControlProperty(session=self._session,
                                  gateway=self.gateway,
                                  element_uid=uid_info['UID'],
                                  key_count=uid_info['properties']['keyCount'],
                                  key_pressed=uid_info['properties']['keyPressed'],
                                  type=uid_info['properties']['type'])

    def _switch_type(self, uid_info: dict):
        """
        Process switch type setting (sts) properties. Interestingly, a switch with two buttons reports a switchType of 1 and a
        switch with four buttons reports a switchType of 2. This confusing behavior is corrected by doubling the value.
        """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding switch type setting to {device_uid}")
        self.devices[device_uid].settings_property['switch_type'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             value=uid_info['properties']['switchType'] * 2)

    def _temperature_report(self, uid_info: dict):
        """ Process temperature report setting (trs) properties. """
        device_uid = get_device_uid_from_setting_uid(uid_info['UID'])
        self._logger.debug(f"Adding temperature report settings to {device_uid}.")
        self.devices[device_uid].settings_property['temperature_report'] = \
            SettingsProperty(session=self._session,
                             gateway=self.gateway,
                             element_uid=uid_info['UID'],
                             temp_report=uid_info['properties']['tempReport'],
                             target_temp_report=uid_info['properties']['targetTempReport'])

    def _unknown(self, uid_info: dict):
        """ Ignore unknown properties. """
        ignore = ("ss", "mcs")
        if not uid_info['UID'].startswith(ignore):
            self._logger.debug(f"Found an unexpected element uid: {uid_info.get('UID')}")
