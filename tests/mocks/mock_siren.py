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

    device = Zwave(**test_data.get("devices").get("siren"))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.binary_sensor_property = {}
    device.binary_sensor_property[f'devolo.SirenBinarySensor:{device_uid}'] = \
        BinarySensorProperty(gateway=gateway,
                             session=session,
                             element_uid=f'devolo.SirenBinarySensor:{device_uid}',
                             state=test_data.get("devices").get("siren").get("state"))

    device.multi_level_switch_property = {}
    device.multi_level_switch_property[f'devolo.SirenMultiLevelSwitch:{device_uid}'] = \
        MultiLevelSwitchProperty(gateway=gateway,
                                 session=session,
                                 element_uid=f'devolo.SirenMultiLevelSwitch:{device_uid}',
                                 state=test_data.get("devices").get("siren").get("state"))

    device.settings_property = {}
    device.settings_property['muted'] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         element_uid=f'bas.{device_uid}',
                         value=test_data.get("devices").get("siren").get("muted"))

    return device
