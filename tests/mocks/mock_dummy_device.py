import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

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

    device = Zwave(**test_data['devices'][key])
    gateway = MockGateway(test_data['gateway']['id'])
    session = requests.Session()

    device.binary_switch_property = {}
    device.binary_switch_property[f"devolo.BinarySwitch:{test_data['devices'][key]['uid']}"] = \
        BinarySwitchProperty(gateway=gateway,
                             session=session,
                             element_uid=f"devolo.BinarySwitch:{test_data['devices'][key]['uid']}",
                             state=test_data['devices'][key]['state'],
                             enabled=test_data['devices'][key]['guiEnabled'])

    device.settings_property = {}
    device.settings_property["general_device_settings"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         element_uid=f"gds.{test_data['devices'][key]['uid']}",
                         icon=test_data['devices'][key]['icon'],
                         name=test_data['devices'][key]['itemName'],
                         zone_id=test_data['devices'][key]['zoneId'])

    return device
