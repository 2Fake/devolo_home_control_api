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

    def test_process_element_uids(self, mock_properties):
        device = self.devices.get("mains").get("uid")
        element_uids = self.devices.get("mains").get("elementUIDs")
        del self.homecontrol.devices['hdm:ZWave:F6BF9812/2'].binary_switch_property
        del self.homecontrol.devices['hdm:ZWave:F6BF9812/2'].consumption_property
        del self.homecontrol.devices['hdm:ZWave:F6BF9812/2'].voltage_property
        assert not hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "binary_switch_property")
        assert not hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "consumption_property")
        assert not hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "voltage_property")
        self.homecontrol._process_element_uids(device, element_uids)
        assert hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "binary_switch_property")
        assert hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "consumption_property")
        assert hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "voltage_property")

    def test_process_element_uids_invalid(self):
        device = self.devices.get("mains").get("uid")
        element_uids = ['fibaro:hdm:ZWave:F6BF9812/2']
        self.homecontrol._process_element_uids(device, element_uids)

    def test_process_settings_uids(self, mock_properties):
        device = self.devices.get("mains").get("uid")
        setting_uids = self.devices.get("mains").get("settingsUIDs")
        self.homecontrol._process_settings_uids(device, setting_uids)

    def test_process_settings_uids_invalid(self):
        device = self.devices.get("mains").get("uid")
        settings_uids = ['fibaro:hdm:ZWave:F6BF9812/2']
        self.homecontrol._process_settings_uids(device, settings_uids)

    def test_process_settings_property_empty(self, mock_properties):
        del self.homecontrol.devices['hdm:ZWave:F6BF9812/2'].settings_property
        assert not hasattr(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'], "settings_property")
        device = self.devices.get("mains").get("uid")
        setting_uids = self.devices.get("mains").get("settingsUIDs")
        self.homecontrol._process_settings_uids(device, setting_uids)
        assert len(self.homecontrol.devices['hdm:ZWave:F6BF9812/2'].settings_property) > 0
