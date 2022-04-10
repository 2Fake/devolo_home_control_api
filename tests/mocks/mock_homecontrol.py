import json
import pathlib

from .mock_dummy_device import dummy_device
from .mock_humidity_sensor_device import humidity_sensor_device
from .mock_metering_plug import metering_plug
from .mock_multi_level_sensor_device import multi_level_sensor_device
from .mock_multi_level_switch_device import multi_level_switch_device
from .mock_remote_control import remote_control
from .mock_shutter import shutter
from .mock_siren import siren


def mock__inspect_devices(self, devices):
    file = pathlib.Path(__file__).parent / ".." / "test_data.json"
    with file.open("r") as fh:
        test_data = json.load(fh)

    mapping = {
        "blinds": shutter,
        "humidity": humidity_sensor_device,
        "mains": metering_plug,
        "multi_level_switch": multi_level_switch_device,
        "remote": remote_control,
        "sensor": multi_level_sensor_device,
        "siren": siren,
    }

    for device_type, device in test_data["devices"].items():
        device_uid = device["uid"]
        self.devices[device_uid] = mapping.get(device_type, dummy_device)(
            device_uid if device_type in mapping else device_type
        )
