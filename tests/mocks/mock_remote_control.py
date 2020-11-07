import json
import pathlib

import requests

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.remote_control_property import RemoteControlProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

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

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data['devices']['remote'])
    gateway = MockGateway(test_data['gateway']['id'], mydevolo=mydevolo)
    session = requests.Session()
    connection = {
        "gateway": gateway,
        "mydevolo": mydevolo,
        "session": session
    }

    device.remote_control_property = {}
    device.settings_property = {}

    device.remote_control_property[f'devolo.RemoteControl:{device_uid}'] = \
        RemoteControlProperty(connection=connection,
                              element_uid=f'devolo.RemoteControl:{device_uid}',
                              key_count=test_data['devices']['remote']['key_count'],
                              key_pressed=0)

    device.settings_property["general_device_settings"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'gds.{device_uid}',
                         icon=test_data['devices']['remote']['icon'],
                         name=test_data['devices']['remote']['itemName'],
                         zone_id=test_data['devices']['remote']['zoneId'])


    device.settings_property["switch_type"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'sts.{device_uid}',
                         value=test_data['devices']['remote']['key_count'])

    return device
