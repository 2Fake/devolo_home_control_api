import json

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


def dummy_device(key: str) -> Zwave:
    """
    Represent a dummy device in tests, where we do not care about the device type

    :param key: Key to look up in test_data.json
    :return: Dummy device
    """
    with open('test_data.json') as file:
        test_data = json.load(file)

    device = Zwave(name=test_data.get("devices").get(key).get("name"),
                   device_uid=test_data.get("devices").get(key).get("uid"),
                   zone=test_data.get("devices").get(key).get("zone_name"),
                   battery_level=-1,
                   icon=test_data.get("devices").get(key).get("icon"),
                   online_state=test_data.get("devices").get(key).get("online"))

    device.binary_switch_property = {}
    device.binary_switch_property[f'devolo.BinarySwitch:{test_data.get("devices").get(key).get("uid")}'] = \
        BinarySwitchProperty(element_uid=f'devolo.BinarySwitch:{test_data.get("devices").get(key).get("uid")}')

    return device
