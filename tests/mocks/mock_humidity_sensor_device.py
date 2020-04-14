import json
import pathlib

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.dewpoint_sensor_property import DewpointSensorProperty
from devolo_home_control_api.properties.humidity_bar_property import HumidityBarProperty
from devolo_home_control_api.properties.mildew_sensor_property import MildewSensorProperty

from .mock_gateway import MockGateway


def humidity_sensor_device(key: str) -> Zwave:
    """
    Represent a humidity sensor

    :param key: Key to look up in test_data.json
    :return: Humidity sensor device
    """
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    device = Zwave(**test_data.get("devices").get(key))
    gateway = MockGateway(test_data.get("gateway").get("id"))
    session = requests.Session()

    device.dewpoint_sensor_property = {}
    device.humidity_bar_property = {}
    device.mildew_sensor_property = {}

    element_uid = f'devolo.DewpointSensor:{test_data.get("devices").get(key).get("uid")}'
    device.dewpoint_sensor_property[element_uid] = \
        DewpointSensorProperty(gateway=gateway,
                               session=session,
                               element_uid=element_uid,
                               value=test_data.get("devices").get(key).get("dewpoint"))

    element_uid = f'devolo.MildewSensor:{test_data.get("devices").get(key).get("uid")}'
    device.mildew_sensor_property[element_uid] = \
        MildewSensorProperty(gateway=gateway,
                             session=session,
                             element_uid=element_uid,
                             state=test_data.get("devices").get(key).get("mildew"))

    element_uid = f'devolo.HumidityBar:{test_data.get("devices").get(key).get("uid")}'
    device.humidity_bar_property[element_uid] = \
        HumidityBarProperty(gateway=gateway,
                            session=session,
                            element_uid=element_uid,
                            zone=test_data.get("devices").get(key).get("zone"),
                            value=test_data.get("devices").get(key).get("value"))

    return device
