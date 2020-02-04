import pytest

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


class TestZwave:
    def test_get_property(self):
        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=-1,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=2)

        device.binary_switch_property = {}
        element_uid = f'devolo.BinarySwitch:{self.devices.get("mains").get("uid")}'
        device.binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)

        assert device.get_property("binary_switch")[0] == f'devolo.BinarySwitch:{self.devices.get("mains").get("uid")}'

    def test_get_property_invalid(self):
        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=-1,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=2)

        with pytest.raises(AttributeError):
            device.get_property("binary_switch")

    def test_battery_level(self):
        # TODO: Use battery driven device
        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=55,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=2)

        assert device.battery_level == 55

    def test_device_online_state_state(self):
        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=-1,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=1)
        assert device.online == "offline"

        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=-1,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=2)
        assert device.online == "online"

        device = Zwave(name=self.devices.get("mains").get("name"),
                       device_uid=self.devices.get("mains").get("uid"),
                       zone=self.devices.get("mains").get("zone"),
                       battery_level=-1,
                       icon=self.devices.get("mains").get("icon"),
                       online_state=27)
        device.online = "unknown state"
