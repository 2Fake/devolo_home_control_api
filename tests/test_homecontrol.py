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
        # TODO: Use test data
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == 2
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2") is None

    def test__binary_switch(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].binary_switch_property
        assert not hasattr(self.homecontrol.devices.get(device), "binary_switch_property")
        self.homecontrol._binary_switch({"UID": "devolo.BinarySwitch:hdm:ZWave:F6BF9812/2", "properties": {"state": 1}})
        assert hasattr(self.homecontrol.devices.get(device), "binary_switch_property")

    def test__general_device(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._general_device({"UID": "gds.hdm:ZWave:F6BF9812/2",
                                          "properties": {"settings": {"events_enabled": True,
                                                                      "name": self.devices.get("mains").get("itemName"),
                                                                      "zoneId": self.devices.get("mains").get("zone_id"),
                                                                      "icon": self.devices.get("mains").get("icon")}}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("general_device_settings"), "events_enabled")

    def test__led(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._led({"UID": "gds.hdm:ZWave:F6BF9812/2", "properties": {"led": True}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("led"), "led_setting")

    def test__consumption(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].consumption_property
        assert not hasattr(self.homecontrol.devices.get(device), "consumption_property")
        self.homecontrol._meter({"UID": "devolo.Meter:hdm:ZWave:F6BF9812/2", "properties": {
                                 "current": self.devices.get("mains").get("current_consumption"),
                                 "total": self.devices.get("mains").get("total_consumption"),
                                 "sinceTime": self.devices.get("mains").get("properties").get("total_consumption")}})
        assert hasattr(self.homecontrol.devices.get(device), "consumption_property")

    def test__parameter(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._parameter({"UID": "cps.hdm:ZWave:F6BF9812/2",
                                     "properties": {"param_changed": False}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("param_changed"), "param_changed")

    def test__protection(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._protection({"UID": "ps.hdm:ZWave:F6BF9812/2",
                                      "properties": {"local_switch": True,
                                                     "remote_switch": False}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("protection"), "local_switching")
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("protection"), "remote_switching")

    def test__voltage_multi_level_sensor(self, mock_properties):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].voltage_property
        assert not hasattr(self.homecontrol.devices.get(device), "voltage_property")
        self.homecontrol._voltage_multi_level_sensor({"UID": "devolo.VoltageMultiLevelSensor:hdm:ZWave:F6BF9812/2",
                                                      "properties": {
                                                          "current": self.devices.get("mains").get("current_consumption")}})
        assert hasattr(self.homecontrol.devices.get(device), "voltage_property")

    def test_device_change_add(self, mocker, mock_inspect_devices):
        uids = [self.devices.get(device).get("uid") for device in self.devices]
        uids.append("test_uid")
        spy = mocker.spy(self.homecontrol, '_inspect_devices')
        self.homecontrol.device_change(uids)
        spy.assert_called_once_with(["test_uid"])

    def test_device_change_remove(self):
        uids = [self.devices.get(device).get("uid") for device in self.devices]
        del uids[2]
        self.homecontrol.device_change(uids)
        assert self.devices.get("mains").get("uid") not in self.homecontrol.devices.keys()

    @pytest.mark.usefixtures("mock_mprmrest_all_devices")
    @pytest.mark.usefixtures("mock_extract_data_from_element_uids")
    def test__inspect_devices(self, mocker):
        spy = mocker.spy(self.homecontrol, '_inspect_devices')
        self.homecontrol._inspect_devices([self.devices.get("mains")])
        assert spy.call_count == 1

    def test__update(self, mocker):
        spy = mocker.spy(self.homecontrol.updater, "update")
        self.homecontrol.update({"properties": {"uid": self.devices.get("mains").get("uid")}})
        spy.assert_called_once_with({"properties": {"uid": self.devices.get("mains").get("uid")}})
