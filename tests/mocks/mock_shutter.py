import json
import pathlib

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.properties.multi_level_switch_property import MultiLevelSwitchProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty


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
    device = Zwave(mydevolo_instance=mydevolo, **test_data["devices"]["blinds"])

    device.multi_level_switch_property = {}
    device.settings_property = {}

    device.multi_level_switch_property[f"devolo.Blinds:{device_uid}"] = MultiLevelSwitchProperty(
        element_uid=f"devolo.Blinds:{device_uid}",
        setter=lambda uid, state: None,
        value=test_data["devices"]["blinds"]["value"],
        max=test_data["devices"]["blinds"]["max"],
        min=test_data["devices"]["blinds"]["min"],
    )

    device.settings_property["i2"] = SettingsProperty(
        element_uid=f"bas.{device_uid}", setter=lambda uid, state: None, value=test_data["devices"]["blinds"]["i2"]
    )

    device.settings_property["general_device_settings"] = SettingsProperty(
        element_uid=f"gds.{device_uid}",
        setter=lambda uid, state: None,
        icon=test_data["devices"]["blinds"]["icon"],
        name=test_data["devices"]["blinds"]["itemName"],
        zone_id=test_data["devices"]["blinds"]["zoneId"],
        zones=test_data["gateway"]["zones"],
    )

    device.settings_property["automatic_calibration"] = SettingsProperty(
        element_uid=f"acs.{device_uid}",
        setter=lambda uid, state: None,
        calibration_status=test_data["devices"]["blinds"]["calibrationStatus"] == 2,
    )

    device.settings_property["movement_direction"] = SettingsProperty(
        element_uid=f"bss.{device_uid}",
        setter=lambda uid, state: None,
        direction=not bool(test_data["devices"]["blinds"]["movement_direction"]),
    )

    device.settings_property["shutter_duration"] = SettingsProperty(
        element_uid=f"mss.{device_uid}",
        setter=lambda uid, state: None,
        shutter_duration=test_data["devices"]["blinds"]["shutter_duration"],
    )

    return device
