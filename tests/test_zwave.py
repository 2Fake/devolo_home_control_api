import pytest

from devolo_home_control_api.devices.zwave import Zwave,\
    get_device_type_from_element_uid, get_device_uid_from_element_uid, get_device_uid_from_setting_uid
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty


@pytest.mark.usefixtures("mock_get_zwave_products")
class TestZwave:
    def test_get_property(self, home_control_instance, mock_mprmrest__extract_data_from_element_uid):
        device = Zwave(**self.devices.get("mains"))

        device.binary_switch_property = {}
        element_uid = f'devolo.BinarySwitch:{self.devices.get("mains").get("uid")}'
        device.binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)

        assert isinstance(device.get_property("binary_switch")[0], BinarySwitchProperty)

    def test_get_property_invalid(self, mydevolo, mock_mydevolo__call):
        device = Zwave(**self.devices.get("mains"))

        with pytest.raises(AttributeError):
            device.get_property("binary_switch")

    def test_battery_level(self, mydevolo, mock_mydevolo__call):
        # TODO: Use battery driven device
        device = Zwave(**self.devices.get("ambiguous_1"))

        assert device.batteryLevel == 55

    def test_device_online_state_state(self, mydevolo, mock_mydevolo__call):
        device = Zwave(**self.devices.get("ambiguous_2"))
        assert device.status == 1

        device = Zwave(**self.devices.get("mains"))
        assert device.status == 2

        device = Zwave(**self.devices.get("ambiguous_1"))
        assert device.status not in [1, 2]

    def test_get_device_type_from_element_uid(self):
        assert get_device_type_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "devolo.Meter"

    def test_get_device_uid_from_setting_uid(self):
        assert get_device_uid_from_setting_uid("lis.hdm:ZWave:EB5A9F6C/2") == "hdm:ZWave:EB5A9F6C/2"

    def test_get_device_uid_from_element_uid(self):
        assert get_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "hdm:ZWave:F6BF9812/2"
