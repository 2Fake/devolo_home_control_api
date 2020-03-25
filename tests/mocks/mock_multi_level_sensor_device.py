import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty

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
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.binary_sensor_property = {}
    device.binary_sensor_property[f'devolo.BinarySensor:{test_data.get("devices").get(key).get("uid")}'] = \
        BinarySensorProperty(gateway=gateway,
                             session=session,
                             element_uid=f'devolo.BinarySensor:{test_data.get("devices").get(key).get("uid")}',
                             state=test_data.get("devices").get("sensor").get("state"))

    return device
