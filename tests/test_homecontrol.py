import pytest

from devolo_home_control_api.homecontrol import get_sub_device_uid_from_element_uid


@pytest.mark.usefixtures("mock_inspect_devices_metering_plug")
@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mydevolo__call")
class TestHomeControl:
    # TODO: Clear devices after each test

    def test_binary_sensor_devices(self):
        assert hasattr(self.homecontrol.binary_sensor_devices[0], "binary_sensor_property")

    def test_binary_switch_devices(self):
        assert hasattr(self.homecontrol.binary_switch_devices[0], "binary_switch_property")

    def test_get_publisher(self):
        assert len(self.homecontrol.publisher._events) == 6

    def test_get_sub_device_uid_from_element_uid(self):
        # TODO: Use test data
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == 2
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2") is None

    def test__binary_sensor(self):
        # TODO: Use test data
        device = self.devices.get("sensor").get("uid")
        del self.homecontrol.devices[device].binary_sensor_property
        assert not hasattr(self.homecontrol.devices.get(device), "binary_sensor_property")
        self.homecontrol._binary_sensor({"UID": self.devices.get("sensor").get("elementUIDs")[0], "properties": {"state": 1}})
        assert hasattr(self.homecontrol.devices.get(device), "binary_sensor_property")

    def test__binary_switch(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].binary_switch_property
        assert not hasattr(self.homecontrol.devices.get(device), "binary_switch_property")
        self.homecontrol._binary_switch({"UID": "devolo.BinarySwitch:hdm:ZWave:F6BF9812/2", "properties": {"state": 1}})
        assert hasattr(self.homecontrol.devices.get(device), "binary_switch_property")

    def test__consumption(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].consumption_property
        assert not hasattr(self.homecontrol.devices.get(device), "consumption_property")
        self.homecontrol._meter({"UID": "devolo.Meter:hdm:ZWave:F6BF9812/2", "properties": {
                                 "current": self.devices.get("mains").get("current_consumption"),
                                 "total": self.devices.get("mains").get("total_consumption"),
                                 "sinceTime": self.devices.get("mains").get("properties").get("total_consumption")}})
        assert hasattr(self.homecontrol.devices.get(device), "consumption_property")

    def test__dewpoint(self):
        # TODO: Use test data
        device = self.devices.get("humidity").get("uid")
        del self.homecontrol.devices[device].dewpoint_sensor_property
        assert not hasattr(self.homecontrol.devices.get(device), "dewpoint_sensor_property")
        self.homecontrol._dewpoint({"UID": self.devices.get("humidity").get("elementUIDs")[1],
                                   "properties": {"value": 24.4, "sensorType": "dewpoint"}})
        assert hasattr(self.homecontrol.devices.get(device), "dewpoint_sensor_property")

    def test__general_device(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._general_device({"UID": "gds.hdm:ZWave:F6BF9812/2",
                                          "properties": {"settings": {"events_enabled": True,
                                                                      "name": self.devices.get("mains").get("itemName"),
                                                                      "zoneId": self.devices.get("mains").get("zone_id"),
                                                                      "icon": self.devices.get("mains").get("icon")}}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("general_device_settings"), "events_enabled")

    def test__humidity_bar(self):
        # TODO: Use test data
        device = self.devices.get("humidity").get("uid")
        del self.homecontrol.devices[device].humidity_bar_property
        assert not hasattr(self.homecontrol.devices.get(device), "humidity_bar_property")
        self.homecontrol._humidity_bar({"UID": f"devolo.HumidityBarValue:{device}",
                                        "properties": {"sensorType": "humidityBarPos", "value": 75}})
        self.homecontrol._humidity_bar({"UID": f"devolo.HumidityBarZone:{device}",
                                        "properties": {"sensorType": "humidityBarZone", "value": 1}})
        assert self.homecontrol.devices.get(device).humidity_bar_property.get(f"devolo.HumidityBar:{device}").value == 75
        assert self.homecontrol.devices.get(device).humidity_bar_property.get(f"devolo.HumidityBar:{device}").zone == 1

    def test__last_activity(self):
        # TODO: Use test data
        device = self.devices.get("sensor").get("uid")
        self.homecontrol._binary_sensor({"UID": self.devices.get("sensor").get("elementUIDs")[0],
                                         "properties": {"state": 1}})
        self.homecontrol._last_activity({"UID": self.devices.get("sensor").get("elementUIDs")[1],
                                         "properties": {"lastActivityTime": 1581419650436}})
        assert hasattr(self.homecontrol.devices[device].binary_sensor_property.
                       get(self.devices.get("sensor").get("elementUIDs")[0]), "last_activity")

    def test__led(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._led({"UID": "gds.hdm:ZWave:F6BF9812/2", "properties": {"led": True}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("led"), "led_setting")
        device = self.devices.get("sensor").get("uid")
        self.homecontrol._led({"UID": "vfs.hdm:ZWave:F6BF9812/6", "properties": {"feedback": True}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("led"), "led_setting")

    def test__mildew(self):
        # TODO: Use test data
        device = self.devices.get("humidity").get("uid")
        del self.homecontrol.devices[device].mildew_sensor_property
        assert not hasattr(self.homecontrol.devices.get(device), "mildew_sensor_property")
        self.homecontrol._mildew({"UID": self.devices.get("humidity").get("elementUIDs")[0],
                                  "properties": {"value": 0, "sensorType": "mildew"}})
        assert hasattr(self.homecontrol.devices.get(device), "mildew_sensor_property")

    def test__motion_sensitivity(self):
        # TODO: Use test data
        device = self.devices.get("sensor").get("uid")
        self.homecontrol._motion_sensitivity({"UID": "mss.hdm:ZWave:F6BF9812/6", "properties": {"value": 60, "targetValue": 60}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("motion_sensitivity"),
                       "motion_sensitivity")
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("motion_sensitivity"),
                       "target_motion_sensitivity")

    def test__multi_level_sensor(self):
        # TODO: Use test data
        device = self.devices.get("sensor").get("uid")
        del self.homecontrol.devices[device].multi_level_sensor_property
        assert not hasattr(self.homecontrol.devices.get(device), "multi_level_sensor_property")
        self.homecontrol._multi_level_sensor({"UID": self.devices.get("sensor").get("elementUIDs")[2],
                                              "properties": {"value": 90.0, "unit": "%", "sensorType": "light"}})
        assert hasattr(self.homecontrol.devices.get(device), "multi_level_sensor_property")

    def test__parameter(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._parameter({"UID": "cps.hdm:ZWave:F6BF9812/2",
                                     "properties": {"param_changed": False}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("param_changed"), "param_changed")

    def test__protection(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        self.homecontrol._protection({"UID": "ps.hdm:ZWave:F6BF9812/2",
                                      "properties": {"local_switch": True,
                                                     "remote_switch": False}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("protection"), "local_switching")
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("protection"), "remote_switching")

    def test__temperature_report(self):
        # TODO: Use test data
        device = self.devices.get("sensor").get("uid")
        self.homecontrol._temperature_report({"UID": "trs.hdm:ZWave:F6BF9812/6",
                                              "properties": {"tempReport": True,
                                                             "targetTempReport": False}})
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("temperature_report"), "temp_report")
        assert hasattr(self.homecontrol.devices.get(device).settings_property.get("temperature_report"), "target_temp_report")

    def test__voltage_multi_level_sensor(self):
        # TODO: Use test data
        device = self.devices.get("mains").get("uid")
        del self.homecontrol.devices[device].voltage_property
        assert not hasattr(self.homecontrol.devices.get(device), "voltage_property")
        self.homecontrol._voltage_multi_level_sensor({"UID": "devolo.VoltageMultiLevelSensor:hdm:ZWave:F6BF9812/2",
                                                      "properties": {
                                                          "current": self.devices.get("mains").get("current_consumption")}})
        assert hasattr(self.homecontrol.devices.get(device), "voltage_property")

    @pytest.mark.usefixtures("mock_inspect_devices")
    def test_device_change_add(self, mocker):
        uids = [self.devices.get(device).get("uid") for device in self.devices]
        uids.append("test_uid")
        spy = mocker.spy(self.homecontrol, '_inspect_devices')
        self.homecontrol.device_change(uids)
        spy.assert_called_once_with(["test_uid"])

    def test_device_change_remove(self):
        uids = [self.devices.get(device).get("uid") for device in self.devices]
        del uids[3]
        self.homecontrol.device_change(uids)
        assert self.devices.get("mains").get("uid") not in self.homecontrol.devices.keys()

    @pytest.mark.usefixtures("mock_extract_data_from_element_uids")
    @pytest.mark.usefixtures("mock_mprmrest_get_all_devices")
    def test__inspect_devices(self, mocker):
        spy = mocker.spy(self.homecontrol, '_inspect_devices')
        self.homecontrol._inspect_devices([self.devices.get("mains")])
        assert spy.call_count == 1
