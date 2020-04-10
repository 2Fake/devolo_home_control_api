import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.humidity_bar_property import HumidityBarProperty

from .mock_gateway import MockGateway


def humidity_bar_device(key: str) -> Zwave:
    """
    Represent a humidity bar

    :param key: Key to look up in test_data.json
    :return: Humidity bar sensor device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get(key))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.humidity_bar_property = {}
    device.settings_property = {}

    element_uid = f'devolo.HumidityBar:{test_data.get("devices").get(key).get("uid")}'
    device.humidity_bar_property[element_uid] = \
        HumidityBarProperty(gateway=gateway,
                            session=session,
                            element_uid=element_uid,
                            zone=test_data.get("devices").get(key).get("zone"),
                            value=test_data.get("devices").get(key).get("value"))

    return device
