import pytest
from datetime import datetime, timezone


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_publisher_dispatch")
class TestUpdater:

    @pytest.mark.usefixtures("mock_updater_binary_switch")
    def test_update_device(self, mocker):
        message = {"properties": {"property.name": "state", "uid": f"devolo.BinarySwitch:{self.devices['mains']['uid']}"}}
        spy = mocker.spy(self.homecontrol.updater, '_binary_switch')
        self.homecontrol.updater.update(message=message)
        spy.assert_called_once_with(message)

    @pytest.mark.usefixtures("mock_updater_pending_operations")
    def test_update_pending_operations(self, mocker):
        message = {"properties": {"property.name": "pendingOperations",
                                  "uid": ""}}
        spy = mocker.spy(self.homecontrol.updater, '_pending_operations')
        self.homecontrol.updater.update(message=message)
        spy.assert_called_once_with(message)

    def test__automatic_calibration(self):
        uid = self.devices['blinds']['uid']
        calibration_status = self.devices['blinds']['calibrationStatus']
        self.homecontrol.updater._automatic_calibration(message={"properties": {
                                                        "uid": f"acs.{uid}",
                                                        "property.value.new": {"status": calibration_status}}})
        assert self.homecontrol.devices[uid].settings_property['automatic_calibration'].calibration_status

    def test__automatic_calibration_key_error(self):
        uid = self.devices['blinds']['uid']
        calibration_status = self.devices['blinds']['calibrationStatus']
        self.homecontrol.updater._automatic_calibration(message={"properties": {
                                                        "uid": f"acs.{uid}",
                                                        "property.value.new": calibration_status}})
        assert self.homecontrol.devices[uid].settings_property['automatic_calibration'].calibration_status

    def test__binary_async_blinds(self):
        uid = self.devices['blinds']['uid']
        self.homecontrol.devices[uid].settings_property['i2'].value = self.devices['blinds']['i2']
        self.homecontrol.updater._binary_async(message={"properties": {
                                               "uid": f"bas.{uid}#i2",
                                               "property.value.new": not self.devices['blinds']['i2']}})
        assert not self.homecontrol.devices[uid].settings_property['i2'].value

    def test__binary_async_siren(self):
        uid = self.devices['siren']['uid']
        self.homecontrol.devices[uid].settings_property['muted'].value = self.devices['siren']['muted']
        self.homecontrol.updater._binary_async(message={"properties": {
                                               "uid": f"bas.{uid}",
                                               "property.value.new": not self.devices['siren']['muted']}})
        assert not self.homecontrol.devices[uid].settings_property['muted'].value

    def test__binary_sensor(self):
        uid = self.devices['sensor']['uid']
        device = self.homecontrol.devices[uid].binary_sensor_property[f"devolo.BinarySensor:{uid}"]
        device.state = True
        state = device.state
        self.homecontrol.updater._binary_sensor(message={"properties":
                                                {"property.name": "state",
                                                 "uid": f"devolo.BinarySensor:{uid}",
                                                 "property.value.new": 0}})
        state_new = device.state
        assert state != state_new
        assert device.last_activity != datetime.fromtimestamp(0)

    def test__binary_sync(self):
        uid = self.devices['blinds']['uid']
        self.homecontrol.updater._binary_sync(message={"properties":
                                              {"uid": f"bss.{uid}",
                                               "property.value.new": self.devices['blinds']['movement_direction']}})
        assert self.homecontrol.devices[uid].settings_property["movement_direction"].direction is \
            bool(self.devices['blinds']['movement_direction'])

    def test__binary_switch(self):
        uid = self.devices.get("mains").get("uid")
        self.homecontrol.devices.get(uid).binary_switch_property \
            .get(f"devolo.BinarySwitch:{uid}").state = True
        state = self.homecontrol.devices.get(uid).binary_switch_property \
            .get(f"devolo.BinarySwitch:{uid}").state
        self.homecontrol.updater._binary_switch(message={"properties":
                                                {"property.name": "targetState",
                                                 "uid": f"devolo.BinarySwitch:{uid}",
                                                 "property.value.new": 0}})
        state_new = self.homecontrol.devices.get(uid).binary_switch_property \
            .get(f"devolo.BinarySwitch:{uid}").state
        assert state != state_new

    def test__device_change(self):
        self.homecontrol.updater.on_device_change = lambda uids: AssertionError()
        try:
            self.homecontrol.updater._device_change(message={"properties":
                                                    {"uid": "devolo.DevicesPage",
                                                     "property.value.new": []}})
            assert False
        except AssertionError:
            assert True

    def test__device_change_error(self, mocker):
        self.homecontrol.updater.on_device_change = None
        spy = mocker.spy(self.homecontrol.updater._logger, "error")
        self.homecontrol.updater._device_change({})
        spy.assert_called_once_with("on_device_change is not set.")

    def test__device_state(self):
        uid = self.devices.get("mains").get("uid")
        online_state = self.homecontrol.devices.get(uid).status
        self.homecontrol.updater._device_state(message={"properties": {"uid": uid,
                                                                       "property.name": "status",
                                                                       "property.value.new": 1}})
        assert self.homecontrol.devices.get(uid).status == 1
        assert online_state != self.homecontrol.devices.get(uid).status

    def test__general_device(self):
        uid = self.devices['mains']['uid']
        events_enabled = self.devices['mains']['properties']['eventsEnabled']
        self.homecontrol.devices[uid].settings_property['general_device_settings'].events_enabled = events_enabled
        self.homecontrol.updater._general_device(message={"properties":
                                                          {"uid": f"gds.{uid}",
                                                           "property.value.new":
                                                           {"eventsEnabled": not events_enabled,
                                                            "icon": self.devices['mains']['properties']['icon'],
                                                            "name": self.devices['mains']['properties']["itemName"],
                                                            "zoneID": self.devices['mains']['properties']["zoneId"]}}})
        assert not self.homecontrol.devices[uid].settings_property['general_device_settings'].events_enabled

    def test__gateway_accessible(self):
        self.homecontrol.gateway.online = True
        self.homecontrol.gateway.sync = True
        accessible = self.homecontrol.gateway.online
        online_sync = self.homecontrol.gateway.sync
        self.homecontrol.updater._gateway_accessible(message={"properties": {"property.name": "gatewayAccessible",
                                                                             "property.value.new": {"accessible": False,
                                                                                                    "onlineSync": False}}})
        accessible_new = self.homecontrol.gateway.online
        online_sync_new = self.homecontrol.gateway.sync
        assert accessible != accessible_new
        assert online_sync != online_sync_new

    def test__grouping(self):
        zone_id = "hz_3"
        name = self.gateway['zones'][zone_id]
        self.homecontrol.updater._grouping(message={"properties":
                                                    {"property.value.new":
                                                     [{"id": zone_id, "name": self.devices['mains']['properties']['zone']}]}})
        assert self.homecontrol.gateway.zones[zone_id] != name
        assert self.homecontrol.gateway.zones[zone_id] == self.devices['mains']['properties']['zone']

    def test__gui_enabled(self):
        uid = self.devices['mains']['uid']
        element_uids = self.devices['mains']['properties']['elementUIDs']
        enabled = self.devices['mains']['properties']['guiEnabled']
        self.homecontrol.devices[uid].binary_switch_property[element_uids[1]].enabled = enabled
        self.homecontrol.updater._gui_enabled(message={"uid": element_uids[0],
                                                       "property.value.new": not enabled})
        assert self.homecontrol.devices[uid].binary_switch_property[element_uids[1]].enabled != enabled

    def test__humidity_bar(self):
        uid = self.devices.get("humidity").get("uid")
        self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value = 75
        self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone = 1
        current_value = self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value
        current_zone = self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone
        self.homecontrol.updater._humidity_bar(message={"properties":
                                               {"uid": f"devolo.HumidityBarValue:{uid}",
                                                "property.value.new": 50}})
        current_value_new = self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value
        self.homecontrol.updater._humidity_bar(message={"properties":
                                               {"uid": f"devolo.HumidityBarZone:{uid}",
                                                "property.value.new": 0}})
        current_zone_new = self.homecontrol.devices.get(uid).humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone

        assert current_value_new == 50
        assert current_zone_new == 0
        assert current_value != current_value_new
        assert current_zone != current_zone_new

    def test__meter(self):
        uid = self.devices.get("mains").get("uid")
        self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").current = 5
        self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").total = 230
        total = self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").total
        # Changing current value
        self.homecontrol.updater._meter(message={"properties": {"property.name": "currentValue",
                                                                "uid": f"devolo.Meter:{uid}",
                                                                "property.value.new": 7}})
        current_new = self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").current
        # Check if current value has changed
        assert current_new == 7
        # Check if total has not changed
        assert total == self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").total
        # Changing total value
        self.homecontrol.updater._meter(message={"properties": {"property.name": "totalValue",
                                                                "uid": f"devolo.Meter:{uid}",
                                                                "property.value.new": 235}})
        total_new = self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").total
        # Check if total value has changed
        assert total_new == 235
        # Check if current value has not changed
        assert self.homecontrol.devices.get(uid).consumption_property \
            .get(f"devolo.Meter:{uid}").current == current_new

    def test__multi_level_sensor(self):
        uid = self.devices['sensor']['uid']
        element_uid = f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)"
        self.homecontrol.devices[uid].multi_level_sensor_property[element_uid].value = 100
        current = self.homecontrol.devices[uid].multi_level_sensor_property[element_uid].value
        self.homecontrol.updater._multi_level_sensor(message={"properties":
                                                     {"uid": element_uid,
                                                      "property.value.new": 50}})
        current_new = self.homecontrol.devices[uid].multi_level_sensor_property[element_uid].value

        assert current_new == 50
        assert current != current_new

    def test__multi_level_switch(self):
        device = self.devices.get("multi_level_switch")
        uid = device.get("uid")
        self.homecontrol.devices.get(uid).multi_level_switch_property \
            .get(device.get("elementUIDs")[0]).value = \
            device.get("value")
        current = self.homecontrol.devices.get(uid).multi_level_switch_property \
            .get(device.get("elementUIDs")[0]).value
        self.homecontrol.updater._multi_level_switch(message={"properties":
                                                     {"uid": device.get("elementUIDs")[0],
                                                      "property.value.new": device.get("max")}})
        current_new = self.homecontrol.devices.get(uid).multi_level_switch_property \
            .get(device.get("elementUIDs")[0]).value

        assert current_new == device.get("max")
        assert current != current_new

    def test__multilevel_sync_sensor(self):
        device = self.devices['sensor']
        uid = device['uid']
        value = device['properties']['value']
        self.homecontrol.devices[uid].settings_property['motion_sensitivity'].motion_sensitivity = value
        self.homecontrol.updater._multilevel_sync(message={"properties":
                                                  {"uid": f"mss.{uid}",
                                                   "property.value.new": value - 1}})
        assert self.homecontrol.devices[uid].settings_property['motion_sensitivity'].motion_sensitivity == value - 1

    def test__multilevel_sync_shutter(self):
        device = self.devices['blinds']
        uid = device['uid']
        value = device['shutter_duration']
        self.homecontrol.devices[uid].settings_property['shutter_duration'].shutter_duration = value
        self.homecontrol.updater._multilevel_sync(message={"properties":
                                                  {"uid": f"mss.{uid}",
                                                   "property.value.new": value - 1}})
        assert self.homecontrol.devices[uid].settings_property['shutter_duration'].shutter_duration == value - 1

    def test__multilevel_sync_siren(self):
        device = self.devices['siren']
        uid = device['uid']
        value = device['properties']['value']
        self.homecontrol.devices[uid].settings_property['tone'].tone = value
        self.homecontrol.updater._multilevel_sync(message={"properties":
                                                  {"uid": f"mss.{uid}",
                                                   "property.value.new": value - 1}})
        assert self.homecontrol.devices[uid].settings_property['tone'].tone == value - 1

    def test__led(self):
        device = self.devices['mains']
        uid = device['uid']
        led_setting = device['properties']['led_setting']
        self.homecontrol.devices[uid].settings_property['led'].led_setting = led_setting
        self.homecontrol.updater._led(message={"properties":
                                               {"uid": f"lis.{uid}",
                                                "property.value.new": not led_setting}})
        assert self.homecontrol.devices[uid].settings_property['led'].led_setting is not led_setting

    def test__parameter(self):
        device = self.devices['mains']
        uid = device['uid']
        param_changed = device['properties']['param_changed']
        self.homecontrol.devices[uid].settings_property['param_changed'].param_changed = param_changed
        self.homecontrol.updater._parameter(message={"properties":
                                                     {"uid": f"cps.{uid}",
                                                      "property.value.new": not param_changed}})
        assert self.homecontrol.devices[uid].settings_property['param_changed'].param_changed is not param_changed

    def test__pending_operations_false(self):
        device = self.devices['mains']
        uid = device['uid']
        pending_operation = device['properties']['pending_operations']
        self.homecontrol.devices[uid].pending_operation = not pending_operation
        self.homecontrol.updater._pending_operations(message={"properties":
                                                              {"uid": device['elementUIDs'][1]}})
        assert self.homecontrol.devices[uid].pending_operation

    def test__pending_operations_true(self):
        device = self.devices['mains']
        uid = device['uid']
        pending_operation = device['properties']['pending_operations']
        self.homecontrol.devices[uid].pending_operation = pending_operation
        self.homecontrol.updater._pending_operations(message={"properties":
                                                              {"uid": device['elementUIDs'][1],
                                                               "property.value.new": {"status": 1}}})
        assert not self.homecontrol.devices[uid].pending_operation

    def test__pending_operations_setting(self):
        device = self.devices['mains']
        uid = device['uid']
        pending_operation = device['properties']['pending_operations']
        self.homecontrol.devices[uid].pending_operation = pending_operation
        self.homecontrol.updater._pending_operations(message={"properties":
                                                              {"uid": device['settingUIDs'][3],
                                                               "property.value.new": {"status": 1}}})
        assert not self.homecontrol.devices[uid].pending_operation

    def test__protection_local(self):
        device = self.devices['mains']
        uid = device['uid']
        local_switch = device['properties']['local_switch']
        self.homecontrol.devices[uid].settings_property['protection'].local_switching = local_switch
        self.homecontrol.updater._protection(message={"properties":
                                                      {"uid": f"ps.{uid}",
                                                       "property.name": "targetLocalSwitch",
                                                       "property.value.new": not local_switch}})
        assert self.homecontrol.devices[uid].settings_property['protection'].local_switching is not local_switch

    def test__protection_remote(self):
        device = self.devices['mains']
        uid = device['uid']
        remote_switch = device['properties']['remote_switch']
        self.homecontrol.devices[uid].settings_property['protection'].remote_switching = remote_switch
        self.homecontrol.updater._protection(message={"properties":
                                                      {"uid": f"ps.{uid}",
                                                       "property.name": "targetRemoteSwitch",
                                                       "property.value.new": not remote_switch}})
        assert self.homecontrol.devices[uid].settings_property['protection'].remote_switching is not remote_switch

    def test__remote_control(self):
        device = self.devices.get("remote")
        uid = device.get("uid")
        self.homecontrol.devices.get(uid).remote_control_property \
            .get(device.get("elementUIDs")[0]).key_pressed = 0
        self.homecontrol.updater._remote_control(message={"properties":
                                                 {"uid": device.get("elementUIDs")[0],
                                                  "property.value.new": 1}})

        assert self.homecontrol.devices.get(uid).remote_control_property \
            .get(device.get("elementUIDs")[0]).key_pressed == 1

    def test__since_time(self):
        device = self.devices['mains']
        uid = device['uid']
        now = datetime.now()
        total_since = self.homecontrol.devices[uid].consumption_property[f'devolo.Meter:{uid}'].total_since
        self.homecontrol.updater._since_time({"uid": f"devolo.Meter:{uid}",
                                              "property.value.new": now.replace(tzinfo=timezone.utc).timestamp() * 1000})
        new_total_since = self.homecontrol.devices[uid].consumption_property[f'devolo.Meter:{uid}'].total_since
        assert total_since != new_total_since
        assert new_total_since == now

    def test__switch_type(self):
        device = self.devices['remote']
        uid = device['uid']
        self.homecontrol.updater._switch_type(message={"properties":
                                                       {"uid": f"sts.{uid}",
                                                        "property.value.new": device['key_count'] / 4}})
        assert self.homecontrol.devices[uid].settings_property['switch_type'].value == device['key_count'] / 2

    def test__temperature(self):
        device = self.devices['sensor']
        uid = device['uid']
        self.homecontrol.devices[uid].settings_property['temperature_report'].temp_report = device['temp_report']
        self.homecontrol.updater._temperature(message={"properties":
                                                       {"uid": f"trs.{uid}",
                                                        "property.value.new": not device['temp_report']}})
        assert self.homecontrol.devices[uid].settings_property['temperature_report'].temp_report is not device['temp_report']

    def test__voltage_multi_level_sensor(self):
        uid = self.devices.get("mains").get("uid")
        self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.VoltageMultiLevelSensor:{uid}").value = 231
        current = self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.VoltageMultiLevelSensor:{uid}").value
        self.homecontrol.updater._voltage_multi_level_sensor(message={"properties":
                                                             {"uid": f"devolo.VoltageMultiLevelSensor:{uid}",
                                                              "property.value.new": 234}})
        current_new = self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.VoltageMultiLevelSensor:{uid}").value

        assert current_new == 234
        assert current != current_new
