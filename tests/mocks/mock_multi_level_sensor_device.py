import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

from .mock_gateway import MockGateway


def multi_level_sensor_device(key: str) -> Zwave:
    """
    Represent a Multi Level Sensor

    :param key: Key to look up in test_data.json
    :return: Multi Level Sensor device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get(key))
    device_uid = test_data.get("devices").get(key).get("uid")
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.binary_sensor_property = {}
    device.multi_level_sensor_property = {}
    device.settings_property = {}

    element_uid = f'devolo.BinarySensor:{device_uid}'
    device.binary_sensor_property[element_uid] = \
        BinarySensorProperty(gateway=gateway,
                             session=session,
                             element_uid=element_uid,
                             state=test_data.get("devices").get(key).get("state"))

    element_uid = f'devolo.MultiLevelSensor:{device_uid}#MultilevelSensor(1)'
    device.multi_level_sensor_property[element_uid] = \
        MultiLevelSensorProperty(gateway=gateway,
                                 session=session,
                                 element_uid=element_uid,
                                 value=test_data.get("devices").get(key).get("value"),
                                 unit=test_data.get("devices").get(key).get("unit"))

    device.settings_property['temperature_report'] = SettingsProperty(gateway=gateway,
                                                                      session=session,
                                                                      element_uid=f"trs.{device_uid}",
                                                                      temp_report=test_data.get("devices").get(key).get(
                                                                          "temp_report"))
    device.settings_property['motion_sensitivity'] = SettingsProperty(gateway=gateway,
                                                                      session=session,
                                                                      element_uid=f"mss.{device_uid}",
                                                                      motion_sensitivity=test_data.get("devices").get(key).get(
                                                                          "motion_sensitivity"))

    return device
