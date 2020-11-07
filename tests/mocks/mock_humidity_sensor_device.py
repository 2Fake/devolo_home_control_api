import json
import pathlib

import requests

from devolo_home_control_api.mydevolo import Mydevolo
from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty
from devolo_home_control_api.properties.humidity_bar_property import HumidityBarProperty
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty
from devolo_home_control_api.properties.settings_property import SettingsProperty

from .mock_gateway import MockGateway


def humidity_sensor_device(device_uid: str) -> Zwave:
    """
    Represent a humidity sensor

    :param device_uid: Device UID this mock shall have
    :return: Humidity sensor device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mydevolo = Mydevolo()
    device = Zwave(mydevolo_instance=mydevolo, **test_data.get("devices").get("humidity"))
    gateway = MockGateway(test_data.get("gateway").get("id"), mydevolo=mydevolo)
    session = requests.Session()
    connection = {
        "gateway": gateway,
        "mydevolo": mydevolo,
        "session": session
    }

    device.binary_sensor_property = {}
    device.humidity_bar_property = {}
    device.multi_level_sensor_property = {}
    device.settings_property = {}

    element_uid = f'devolo.DewpointSensor:{device_uid}'
    device.multi_level_sensor_property[element_uid] = \
        MultiLevelSensorProperty(connection=connection,
                                 element_uid=element_uid,
                                 value=test_data.get("devices").get("humidity").get("dewpoint"))

    element_uid = f'devolo.MildewSensor:{device_uid}'
    device.binary_sensor_property[element_uid] = \
        BinarySensorProperty(connection=connection,
                             element_uid=element_uid,
                             state=test_data.get("devices").get("humidity").get("mildew"))

    element_uid = f'devolo.HumidityBar:{device_uid}'
    device.humidity_bar_property[element_uid] = \
        HumidityBarProperty(connection=connection,
                            element_uid=element_uid,
                            zone=test_data.get("devices").get("humidity").get("zone"),
                            value=test_data.get("devices").get("humidity").get("value"))

    device.settings_property["general_device_settings"] = \
        SettingsProperty(connection=connection,
                         element_uid=f'gds.{test_data.get("devices").get("humidity").get("uid")}',
                         icon=test_data.get("devices").get("humidity").get("icon"),
                         name=test_data.get("devices").get("humidity").get("itemName"),
                         zone_id=test_data.get("devices").get("humidity").get("zoneId"))

    return device
