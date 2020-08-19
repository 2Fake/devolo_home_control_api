import pytest
from datetime import datetime, timezone


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_publisher_dispatch")
class TestUpdater:
    # TODO: Check, if all test cases here are needed. Some seem redundant.

    def test_update_binary_switch_state_valid(self, fill_device_data):
        uid = self.devices.get("mains").get("uid")
        binary_switch_property = self.homecontrol.devices.get(uid).binary_switch_property
        state = binary_switch_property.get(f"devolo.BinarySwitch:{uid}").state
        self.homecontrol.updater.update_binary_switch_state(element_uid=f"devolo.BinarySwitch:{uid}",
                                                            value=True)
        assert state != binary_switch_property.get(f"devolo.BinarySwitch:{uid}").state

    def test_update_binary_switch_state_group(self, fill_device_data):
        try:
            self.homecontrol.updater.update_binary_switch_state(element_uid="devolo.BinarySwitch:devolo.smartGroup.1",
                                                                value=True)
            assert True
        except KeyError:
            assert False

    def test_update_consumption_valid(self, fill_device_data):
        uid = self.devices.get("mains").get("uid")
        consumption_property = self.homecontrol.devices.get(uid).consumption_property
        current_before = consumption_property.get(f"devolo.Meter:{uid}").current
        total_before = consumption_property.get(f"devolo.Meter:{uid}").total
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{uid}",
                                                    consumption="current", value=1.58)
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{uid}",
                                                    consumption="total", value=254)
        assert current_before != consumption_property.get(f"devolo.Meter:{uid}").current
        assert total_before != consumption_property.get(f"devolo.Meter:{uid}").total
        assert consumption_property.get(f"devolo.Meter:{uid}").current == 1.58
        assert consumption_property.get(f"devolo.Meter:{uid}").total == 254

    def test_update_humidity_bar(self, fill_device_data):
        uid = self.devices.get("humidity").get("uid")
        humidity_bar_property = self.homecontrol.devices.get(uid).humidity_bar_property
        current_zone = \
            humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone
        current_value = \
            humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value
        self.homecontrol.updater.update_humidity_bar(element_uid=f"devolo.HumidityBar:{uid}",
                                                     zone=2)
        self.homecontrol.updater.update_humidity_bar(element_uid=f"devolo.HumidityBar:{uid}",
                                                     value=50)
        assert current_zone != \
            humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone
        assert humidity_bar_property.get(f"devolo.HumidityBar:{uid}").zone == 2
        assert current_value != \
            humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value
        assert humidity_bar_property.get(f"devolo.HumidityBar:{uid}").value == 50

    def test_update_multi_level_sensor_valid(self, fill_device_data):
        uid = self.devices.get("sensor").get("uid")
        multi_level_sensor_property = self.homecontrol.devices.get(uid).multi_level_sensor_property
        value_before = multi_level_sensor_property.get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value
        self.homecontrol.updater.update_multi_level_sensor(element_uid=f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)",
                                                           value=50)
        assert value_before != multi_level_sensor_property.get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value
        assert multi_level_sensor_property.get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value == 50

    def test_update_multi_level_switch_state_group(self, fill_device_data):
        try:
            self.homecontrol.updater.update_multi_level_switch(element_uid="devolo.MultiLevelSwitch:devolo.smartGroup.1",
                                                               value=True)
            assert True
        except KeyError:
            assert False

    def test_device_online_state(self):
        uid = self.devices.get("mains").get("uid")
        online_state = self.homecontrol.devices.get(uid).status
        self.homecontrol.updater.update_device_online_state(device_uid=self.devices.get('mains').get('uid'),
                                                            value=1)
        assert self.homecontrol.devices.get(uid).status == 1
        assert self.homecontrol.devices.get(uid).status != online_state

    def test_update_gateway_state(self):
        self.homecontrol.updater.update_gateway_state(accessible=True, online_sync=False)
        assert self.homecontrol.gateway.online
        assert not self.homecontrol.gateway.sync

    def test_update_voltage_valid(self, fill_device_data):
        uid = self.devices.get("mains").get("uid")
        voltage_property = self.homecontrol.devices.get(uid).multi_level_sensor_property
        current_voltage = \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{uid}").value
        self.homecontrol.updater.update_voltage(element_uid=f"devolo.VoltageMultiLevelSensor:{uid}",
                                                value=257)
        assert current_voltage != \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{uid}").value
        assert voltage_property.get(f"devolo.VoltageMultiLevelSensor:{uid}").value == 257

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

    def test__binary_sensor_with_timestamp(self):
        uid = self.devices['sensor']['uid']
        device = self.homecontrol.devices.get(uid).binary_sensor_property[f"devolo.BinarySensor:{uid}"]
        now = datetime.now()
        device.state = True
        state = device.state
        self.homecontrol.updater._binary_sensor(message={"properties":
                                                {"property.name": "state",
                                                 "uid": f"devolo.BinarySensor:{uid}",
                                                 "property.value.new": 0,
                                                 "timestamp": now.replace(tzinfo=timezone.utc).timestamp() * 1000}})
        state_new = device.state
        assert state != state_new
        assert device.last_activity == now

    def test__binary_sensor_without_timestamp(self):
        uid = self.devices['sensor']['uid']
        device = self.homecontrol.devices.get(uid).binary_sensor_property[f"devolo.BinarySensor:{uid}"]
        device.state = True
        state = device.state
        self.homecontrol.updater._binary_sensor(message={"properties":
                                                {"property.name": "state",
                                                 "uid": f"devolo.BinarySensor:{uid}",
                                                 "property.value.new": 0}})
        state_new = device.state
        assert state != state_new
        assert device.last_activity != datetime.fromtimestamp(0)

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

    def test__device_online_state(self):
        uid = self.devices.get("mains").get("uid")
        online_state = self.homecontrol.devices.get(uid).status
        self.homecontrol.updater._device_online_state(message={"properties": {"uid": uid,
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
        uid = self.devices.get("sensor").get("uid")
        self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value = 100
        current = self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value
        self.homecontrol.updater._multi_level_sensor(message={"properties":
                                                     {"uid": f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)",
                                                      "property.value.new": 50}})
        current_new = self.homecontrol.devices.get(uid).multi_level_sensor_property \
            .get(f"devolo.MultiLevelSensor:{uid}#MultilevelSensor(1)").value

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

    def test__multilevel_sync_siren(self):
        device = self.devices['siren']
        uid = device['uid']
        value = device['properties']['value']
        self.homecontrol.devices[uid].settings_property['tone'].tone = value
        self.homecontrol.updater._multilevel_sync(message={"properties":
                                                  {"uid": f"mss.{uid}",
                                                   "property.value.new": value - 1}})
        assert self.homecontrol.devices[uid].settings_property['tone'].tone == value - 1

    def test__last_activity_sensor(self):
        device = self.devices['sensor']
        uid = device['uid']
        last_activity = device['last_activity']
        self.homecontrol.devices[uid].binary_sensor_property[f'devolo.BinarySensor:{uid}'].last_activity = last_activity
        self.homecontrol.updater._last_activity(message={"properties":
                                                {"uid": f"devolo.LastActivity:{uid}",
                                                 "property.value.new": last_activity + 1000}})
        assert self.homecontrol.devices[uid].binary_sensor_property[f'devolo.BinarySensor:{uid}'].last_activity.second \
            - datetime.utcfromtimestamp(last_activity / 1000).second == 1

    def test__last_activity_siren(self):
        device = self.devices['siren']
        uid = device['uid']
        last_activity = device['last_activity']
        self.homecontrol.devices[uid].binary_sensor_property[f'devolo.SirenBinarySensor:{uid}'].last_activity = last_activity
        self.homecontrol.updater._last_activity(message={"properties":
                                                {"uid": f"devolo.LastActivity:{uid}",
                                                 "property.value.new": last_activity + 1000}})
        assert self.homecontrol.devices[uid].binary_sensor_property[f'devolo.SirenBinarySensor:{uid}'].last_activity.second \
            - datetime.utcfromtimestamp(last_activity / 1000).second == 1

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

    def test__temperature(self):
        device = self.devices['sensor']
        uid = device['uid']
        self.homecontrol.devices[uid].settings_property['temperature_report'].temp_report = device['temp_report']
        self.homecontrol.updater._temperature({"properties":
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
