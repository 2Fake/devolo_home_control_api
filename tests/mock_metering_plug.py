from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


def metering_plug(device_uid):
    device = Zwave(name="Light",
                   device_uid=device_uid,
                   zone="Room",
                   battery_level=-1,
                   icon="light-bulb")

    device.binary_switch_property = {}
    device.consumption_property = {}
    device.settings_property = {}

    device.binary_switch_property[f'devolo.BinarySwitch:{device_uid}'] = BinarySwitchProperty(element_uid=f"devolo.BinarySwitch:{device_uid}")
    device.consumption_property[f'devolo.Meter:{device_uid}'] = ConsumptionProperty(element_uid=f"devolo.Meter:{device_uid}")
    device.settings_property[f'cps.{device_uid}'] = SettingsProperty(element_uid=f"cps.{device_uid}")
    device.settings_property[f'gds.{device_uid}'] = SettingsProperty(element_uid=f"gds.{device_uid}")
    device.settings_property[f'lis.{device_uid}'] = SettingsProperty(element_uid=f"lis.{device_uid}")
    device.settings_property[f'ps.{device_uid}'] = SettingsProperty(element_uid=f"ps.{device_uid}")

    return device
