import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty

from .mock_gateway import MockGateway


def dummy_device(key: str) -> Zwave:
    """
    Represent a dummy device in tests, where we do not care about the device type

    :param key: Key to look up in test_data.json
    :return: Dummy device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get(key))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.binary_switch_property = {}
    device.binary_switch_property[f'devolo.BinarySwitch:{test_data.get("devices").get(key).get("uid")}'] = \
        BinarySwitchProperty(gateway=gateway,
                             session=session,
                             element_uid=f'devolo.BinarySwitch:{test_data.get("devices").get(key).get("uid")}',
                             state=test_data.get("devices").get("mains").get("state"))

    return device
