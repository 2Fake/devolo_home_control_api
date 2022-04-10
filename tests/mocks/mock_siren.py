import json
import pathlib

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


def siren(device_uid: str) -> Zwave:
    """
    Represent a siren in tests

    :param device_uid: Device UID this mock shall have
    :return: Siren device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data["devices"]["siren"])

    device.multi_level_switch_property = {}
    device.multi_level_switch_property[f"devolo.SirenMultiLevelSwitch:{device_uid}"] = MultiLevelSwitchProperty(
        element_uid=f"devolo.SirenMultiLevelSwitch:{device_uid}",
        setter=lambda uid, state: None,
        state=test_data["devices"]["siren"]["state"],
    )

    device.settings_property = {}
    device.settings_property["muted"] = SettingsProperty(
        element_uid=f"bas.{device_uid}", setter=lambda uid, state: True, value=test_data["devices"]["siren"]["muted"]
    )

    device.settings_property["general_device_settings"] = SettingsProperty(
        element_uid=f"gds.{device_uid}",
        setter=lambda uid, state: None,
        icon=test_data["devices"]["siren"]["icon"],
        name=test_data["devices"]["siren"]["itemName"],
        zone_id=test_data["devices"]["siren"]["zoneId"],
        zones=test_data["gateway"]["zones"],
    )

    device.settings_property["tone"] = SettingsProperty(
        element_uid=f"mss.{device_uid}",
        setter=lambda uid, state: None,
        value=test_data["devices"]["siren"]["properties"]["value"],
    )

    return device
