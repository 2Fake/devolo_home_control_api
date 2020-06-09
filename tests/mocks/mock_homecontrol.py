import json
import pathlib

from .mock_dummy_device import dummy_device
from .mock_humidity_sensor_device import humidity_sensor_device
from .mock_metering_plug import metering_plug
from .mock_multi_level_sensor_device import multi_level_sensor_device
from .mock_multi_level_switch_device import multi_level_switch_device
from .mock_shutter import shutter
from .mock_siren import siren


def mock__inspect_devices(self, devices):
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    for device_type, device in test_data.get("devices").items():
        device_uid = device.get("uid")
        if device_type == "blinds":
            self.devices[device_uid] = shutter(device_uid=device_uid)
        elif device_type == "humidity":
            self.devices[device_uid] = humidity_sensor_device(key=device_type)
        elif device_type == "mains":
            self.devices[device_uid] = metering_plug(device_uid=device_uid)
        elif device_type == "multi_level_switch":
            self.devices[device_uid] = multi_level_switch_device(device_uid=device_uid)
        elif device_type == "sensor":
            self.devices[device_uid] = multi_level_sensor_device(key=device_type)
        elif device_type == "siren":
            self.devices[device_uid] = siren(device_uid=device_uid)
        else:
            self.devices[device_uid] = dummy_device(key=device_type)
