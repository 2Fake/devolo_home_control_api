import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty

from .mock_gateway import MockGateway


def shutter(device_uid: str) -> Zwave:
    """
    Represent a shutter in tests

    :param device_uid: Device UID this mock shall have
    :return: Metering Plug device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get("blinds"))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.multi_level_switch_property = {}

    device.multi_level_switch_property[f'devolo.Blinds:{device_uid}'] = \
        MultiLevelSwitchProperty(gateway=gateway,
                                 session=session,
                                 element_uid=f"devolo.Blinds:{device_uid}",
                                 value=test_data.get("devices").get("blinds").get("value"),
                                 max=test_data.get("devices").get("blinds").get("max"),
                                 min=test_data.get("devices").get("blinds").get("min"))

    return device
