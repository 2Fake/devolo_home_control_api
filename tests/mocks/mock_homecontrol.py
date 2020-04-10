import json
import pathlib

from .mock_dummy_device import dummy_device
from .mock_humidity_bar_device import humidity_bar_device
from .mock_metering_plug import metering_plug
from .mock_multi_level_sensor_device import multi_level_sensor_device


def mock__inspect_devices(self, devices):
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    for device_type, device in test_data.get("devices").items():
        device_uid = device.get("uid")
        if device_type == "humidity":
            self.devices[device_uid] = humidity_bar_device(key=device_type)
        elif device_type == "mains":
            self.devices[device_uid] = metering_plug(device_uid=device_uid)
        elif device_type == "sensor":
            self.devices[device_uid] = multi_level_sensor_device(key=device_type)
        else:
            self.devices[device_uid] = dummy_device(key=device_type)
