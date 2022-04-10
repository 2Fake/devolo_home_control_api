import json
import pathlib

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.properties.remote_control_property import RemoteControlProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


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
    device = Zwave(mydevolo_instance=mydevolo, **test_data["devices"]["remote"])

    device.remote_control_property = {}
    device.settings_property = {}

    device.remote_control_property[f"devolo.RemoteControl:{device_uid}"] = RemoteControlProperty(
        element_uid=f"devolo.RemoteControl:{device_uid}",
        setter=lambda uid, state: True,
        key_count=test_data["devices"]["remote"]["key_count"],
        key_pressed=0,
    )

    device.settings_property["general_device_settings"] = SettingsProperty(
        element_uid=f"gds.{device_uid}",
        setter=lambda uid, state: None,
        icon=test_data["devices"]["remote"]["icon"],
        name=test_data["devices"]["remote"]["itemName"],
        zone_id=test_data["devices"]["remote"]["zoneId"],
        zones=test_data["gateway"]["zones"],
    )

    device.settings_property["switch_type"] = SettingsProperty(
        element_uid=f"sts.{device_uid}", setter=lambda uid, state: None, value=test_data["devices"]["remote"]["key_count"]
    )

    return device
