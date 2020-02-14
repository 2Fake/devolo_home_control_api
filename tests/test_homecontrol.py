import pytest
from devolo_home_control_api.homecontrol import get_sub_device_uid_from_element_uid


@pytest.mark.usefixtures("mock_inspect_devices_metering_plug")
@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestHomeControl:
    def test_binary_switch_devices(self):
        assert hasattr(self.homecontrol.binary_switch_devices[0], "binary_switch_property")

    def test_get_publisher(self):
        assert len(self.homecontrol.publisher._events) == 3

    def test_is_online(self):
        assert self.homecontrol.is_online(self.devices.get("mains").get("uid"))
        assert not self.homecontrol.is_online(self.devices.get("ambiguous_2").get("uid"))

    def test_get_sub_device_uid_from_element_uid(self):
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == 2
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2") is None
