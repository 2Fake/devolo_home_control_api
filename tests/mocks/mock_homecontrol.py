import json

from .mock_dummy_device import dummy_device
from .mock_metering_plug import metering_plug


def mock__inspect_devices(self):
    with open('test_data.json') as file:
        test_data = json.load(file)

    for device_type, device in test_data.get("devices").items():
        device_uid = device.get("uid")
        if device_type == "mains":
            self.devices[device_uid] = metering_plug(device_uid=device_uid)
        else:
            self.devices[device_uid] = dummy_device(key=device_type)
