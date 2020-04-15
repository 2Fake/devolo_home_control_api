import json
import pathlib

import pytest


file = pathlib.Path(__file__).parent / "test_data.json"
with file.open("r") as fh:
    test_data = json.load(fh)


pytest_plugins = ['tests.fixtures.gateway',
                  'tests.fixtures.homecontrol',
                  'tests.fixtures.mprm',
                  'tests.fixtures.mydevolo',
                  'tests.fixtures.publisher',
                  'tests.fixtures.requests',
                  'tests.fixtures.socket']


@pytest.fixture(autouse=True)
def test_data_fixture(request):
    """ Load test data. """
    request.cls.user = test_data.get("user")
    request.cls.gateway = test_data.get("gateway")
    request.cls.devices = test_data.get("devices")


@pytest.fixture()
def fill_device_data(request):
    """ Load test device data. """
    consumption_property = request.cls.homecontrol.devices.get(test_data.get("devices").get("mains").get("uid")) \
        .consumption_property
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").current = 0.58
    consumption_property.get(f"devolo.Meter:{test_data.get('devices').get('mains').get('uid')}").total = 125.68

    binary_sensor_property = request.cls.homecontrol.devices.get(test_data.get("devices").get("sensor").get("uid")) \
        .binary_sensor_property
    binary_sensor_property.get(f"devolo.BinarySensor:{test_data.get('devices').get('sensor').get('uid')}").state = False

    binary_switch_property = \
        request.cls.homecontrol.devices.get(test_data.get("devices").get("mains").get("uid")).binary_switch_property
    binary_switch_property.get(f"devolo.BinarySwitch:{test_data.get('devices').get('mains').get('uid')}").state = False

    humidity_bar_property = request.cls.homecontrol.devices.get(test_data.get("devices").get("humidity").get("uid")) \
        .humidity_bar_property
    humidity_bar_property.get(f"devolo.HumidityBar:{test_data.get('devices').get('humidity').get('uid')}").zone = 1
    humidity_bar_property.get(f"devolo.HumidityBar:{test_data.get('devices').get('humidity').get('uid')}").value = 75

    voltage_property = request.cls.homecontrol.devices.get(test_data.get("devices").get("mains").get("uid")).voltage_property
    voltage_property.get(f"devolo.VoltageMultiLevelSensor:{test_data.get('devices').get('mains').get('uid')}").current = 236
