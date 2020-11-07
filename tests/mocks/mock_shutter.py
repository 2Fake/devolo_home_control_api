import json
import pathlib

import requests

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

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

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data['devices']['blinds'])
    gateway = MockGateway(test_data['gateway']['id'], mydevolo=mydevolo)
    session = requests.Session()
    connection = {
        "gateway": gateway,
        "mydevolo": mydevolo,
        "session": session
    }

    device.multi_level_switch_property = {}
    device.settings_property = {}

    device.multi_level_switch_property[f'devolo.Blinds:{device_uid}'] = \
        MultiLevelSwitchProperty(connection=connection,
                                 element_uid=f"devolo.Blinds:{device_uid}",
                                 value=test_data['devices']['blinds']['value'],
                                 max=test_data['devices']['blinds']['max'],
                                 min=test_data['devices']['blinds']['min'])

    device.settings_property['i2'] = \
        SettingsProperty(connection=connection,
                         element_uid=f"bas.{device_uid}",
                         value=test_data['devices']['blinds']['i2'])

    device.settings_property["general_device_settings"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'gds.{device_uid}',
                         icon=test_data['devices']['blinds']['icon'],
                         name=test_data['devices']['blinds']['itemName'],
                         zone_id=test_data['devices']['blinds']['zoneId'])

    device.settings_property["automatic_calibration"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'acs.{device_uid}',
                         calibration_status=test_data['devices']['blinds']['calibrationStatus'] == 2)

    device.settings_property["movement_direction"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'bss.{device_uid}',
                         direction=not bool(test_data['devices']['blinds']['movement_direction']))

    device.settings_property["shutter_duration"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'mss.{device_uid}',
                         shutter_duration=test_data['devices']['blinds']['shutter_duration'])

    return device
