import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

from .mock_gateway import MockGateway


def siren(device_uid: str) -> Zwave:
    """
    Represent a siren in tests

    :param device_uid: Device UID this mock shall have
    :return: Siren device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data['devices']['siren'])
    gateway = MockGateway(test_data['gateway']['id'])
    session = requests.Session()

    device.multi_level_switch_property = {}
    device.multi_level_switch_property[f'devolo.SirenMultiLevelSwitch:{device_uid}'] = \
        MultiLevelSwitchProperty(gateway=gateway,
                                 session=session,
                                 element_uid=f"devolo.SirenMultiLevelSwitch:{device_uid}",
                                 state=test_data['devices']['siren']['state'])

    device.settings_property = {}
    device.settings_property['muted'] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         element_uid=f"bas.{device_uid}",
                         value=test_data['devices']['siren']['muted'])
    device.settings_property["general_device_settings"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         element_uid=f"gds.{device_uid}",
                         icon=test_data['devices']['siren']['icon'],
                         name=test_data['devices']['siren']['itemName'],
                         zone_id=test_data['devices']['siren']['zoneId'])

    device.settings_property["tone"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         element_uid=f"mss.{device_uid}",
                         value=test_data['devices']['siren']['properties']['value'])

    return device
