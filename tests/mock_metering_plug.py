import json

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.voltage_property import VoltageProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


def metering_plug(device_uid):
    with open('test_data.json') as file:
        test_data = json.load(file)

    device = Zwave(name=test_data.get("device").get("mains").get("name"),
                   device_uid=device_uid,
                   zone=test_data.get("device").get("mains").get("zone_name"),
                   battery_level=-1,
                   icon=test_data.get("device").get("mains").get("icon"))

    device.binary_switch_property = {}
    device.consumption_property = {}
    device.voltage_property = {}
    device.settings_property = {}

    device.binary_switch_property[f'devolo.BinarySwitch:{device_uid}'] = BinarySwitchProperty(element_uid=f"devolo.BinarySwitch:{device_uid}")
    device.consumption_property[f'devolo.Meter:{device_uid}'] = ConsumptionProperty(element_uid=f"devolo.Meter:{device_uid}")
    device.voltage_property[f'devolo.VoltageMultiLevelSensor:{device_uid}'] = \
        VoltageProperty(element_uid=f"devolo.VoltageMultiLevelSensor:{device_uid}")
    device.settings_property["param_changed"] = SettingsProperty(element_uid=f"cps.{device_uid}")
    device.settings_property["general_device_settings"] = SettingsProperty(element_uid=f"gds.{device_uid}")
    device.settings_property["led"] = SettingsProperty(element_uid=f"lis.{device_uid}")
    device.settings_property["protection_setting"] = SettingsProperty(element_uid=f"ps.{device_uid}")

    return device
