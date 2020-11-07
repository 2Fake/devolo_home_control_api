import json
import pathlib

import requests

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

from .mock_gateway import MockGateway


def multi_level_switch_device(device_uid: str) -> Zwave:
    """
    Represent a multi level switch device in tests

    :param device_uid: Device UID this mock shall have
    :return: Multi level switch device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data.get("devices").get("multi_level_switch"))
    gateway = MockGateway(test_data.get("gateway").get("id"), mydevolo=mydevolo)
    session = requests.Session()

    device.multi_level_switch_property = {}
    device.settings_property = {}

    device.multi_level_switch_property[f'devolo.MultiLevelSwitch:{device_uid}'] = \
        MultiLevelSwitchProperty(gateway=gateway,
                                 session=session,
                                 mydevolo=mydevolo,
                                 element_uid=f"devolo.MultiLevelSwitch:{device_uid}",
                                 value=test_data.get("devices").get("multi_level_switch").get("value"),
                                 max=test_data.get("devices").get("multi_level_switch").get("max"),
                                 min=test_data.get("devices").get("multi_level_switch").get("min"))

    device.settings_property["general_device_settings"] = \
        SettingsProperty(gateway=gateway,
                         session=session,
                         mydevolo=mydevolo,
                         element_uid=f'gds.{device_uid}',
                         icon=test_data.get("devices").get("multi_level_switch").get("icon"),
                         name=test_data.get("devices").get("multi_level_switch").get("itemName"),
                         zone_id=test_data.get("devices").get("multi_level_switch").get("zoneId"))

    return device
