import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.remote_control_property import RemoteControlProperty

from .mock_gateway import MockGateway


def remote_control(device_uid: str) -> Zwave:
    """
    Represent a remote control in tests.

    :param device_uid: Device UID this mock shall have
    :return: Remote Control
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get("remote"))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.remote_control_property = {}
    device.remote_control_property[f'devolo.RemoteControl:{device_uid}'] = \
        RemoteControlProperty(gateway=gateway,
                              session=session,
                              element_uid=f'devolo.RemoteControl:{device_uid}',
                              key_count=test_data.get("devices").get("remote").get("key_count"),
                              key_pressed=0)

    return device