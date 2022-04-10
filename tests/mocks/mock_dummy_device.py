import json
import pathlib

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


def dummy_device(key: str) -> Zwave:
    """
    Represent a dummy device in tests, where we do not care about the device type

    :param key: Key to look up in test_data.json
    :return: Dummy device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data["devices"][key])

    device.binary_switch_property = {}
    device.binary_switch_property[f"devolo.BinarySwitch:{test_data['devices'][key]['uid']}"] = BinarySwitchProperty(
        element_uid=f"devolo.BinarySwitch:{test_data['devices'][key]['uid']}",
        setter=lambda uid, state: None,
        state=test_data["devices"][key]["state"],
        enabled=test_data["devices"][key]["guiEnabled"],
    )

    device.settings_property = {}
    device.settings_property["general_device_settings"] = SettingsProperty(
        element_uid=f"gds.{test_data['devices'][key]['uid']}",
        setter=lambda uid, state: None,
        icon=test_data["devices"][key]["icon"],
        name=test_data["devices"][key]["itemName"],
        zone_id=test_data["devices"][key]["zoneId"],
        zones=test_data.get("gateway").get("zones"),
    )

    return device
