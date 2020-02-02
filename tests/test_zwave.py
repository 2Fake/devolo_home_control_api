import pytest

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


class TestZwave:
    def test_get_property(self):
        device = Zwave(name=self.devices.get('mains').get('name'),
                       device_uid=self.devices.get('mains').get('uid'),
                       zone=self.devices.get('mains').get('zone'),
                       battery_level=-1,
                       icon=self.devices.get('mains').get('icon'))

        device.binary_switch_property = {}
        element_uid = f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}"
        device.binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)

        assert device.get_property("binary_switch")[0] == f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}"

    def test_get_property_invalid(self):
        device = Zwave(name=self.devices.get('mains').get('name'),
                       device_uid=self.devices.get('mains').get('uid'),
                       zone=self.devices.get('mains').get('zone'),
                       battery_level=-1,
                       icon=self.devices.get('mains').get('icon'))

        with pytest.raises(AttributeError):
            device.get_property("binary_switch")
