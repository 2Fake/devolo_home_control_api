import pytest


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_publisher_dispatch")
class TestUpdater:
    def test_update_binary_switch_state_valid(self, fill_device_data):
        binary_switch_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).binary_switch_property
        state = binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
        self.homecontrol.updater.update_binary_switch_state(element_uid=f"devolo.BinarySwitch:"
                                                                        f"{self.devices.get('mains').get('uid')}",
                                                            value=True)
        assert state != binary_switch_property.get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state

    def test_update_consumption_valid(self, fill_device_data):
        consumption_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).consumption_property
        current_before = consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current
        total_before = consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                    consumption="current", value=1.58)
        self.homecontrol.updater.update_consumption(element_uid=f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                    consumption="total", value=254)
        assert current_before != consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current
        assert total_before != consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        assert consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current == 1.58
        assert consumption_property.get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total == 254

    def test_device_online_state(self):
        online_state = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status
        self.homecontrol.updater.update_device_online_state(uid=self.devices.get('mains').get('uid'),
                                                            value=1)
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status == 1
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status != online_state

    def test_update_gateway_state(self):
        self.homecontrol.updater.update_gateway_state(accessible=True, online_sync=False)
        assert self.homecontrol._gateway.online
        assert not self.homecontrol._gateway.sync

    def test_update_voltage_valid(self, fill_device_data):
        voltage_property = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).voltage_property
        current_voltage = \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current
        self.homecontrol.updater.update_voltage(element_uid=f"devolo.VoltageMultiLevelSensor:"
                                                            f"{self.devices.get('mains').get('uid')}",
                                                value=257)
        assert current_voltage != \
            voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current
        assert voltage_property.get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current == 257

    def test_update(self):
        self.homecontrol.updater.update(message={"properties":
                                        {"uid": f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}"}})

    def test_update_invalid(self):
        self.homecontrol.updater.update(message={"properties":
                                        {"uid": "fibaro"}})

    def test__binary_switch(self):
        self.homecontrol.devices.get(self.devices.get('mains').get("uid")).binary_switch_property \
            .get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state = True
        state = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).binary_switch_property \
            .get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
        self.homecontrol.updater._binary_switch(message={"properties": {"property.name": "state",
                                                                        "uid": f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}",
                                                                        "property.value.new": 0}})
        state_new = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).binary_switch_property \
            .get(f"devolo.BinarySwitch:{self.devices.get('mains').get('uid')}").state
        assert state != state_new

    def test__device_online_state(self):
        online_state = self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status
        self.homecontrol.updater._device_online_state(message={"properties": {"uid": self.devices.get('mains').get('uid'),
                                                                              "property.value.new": 1}})
        assert self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status == 1
        assert online_state != self.homecontrol.devices.get(self.devices.get("mains").get("uid")).status

    def test__gateway_accessible(self):
        self.homecontrol._gateway.online = True
        self.homecontrol._gateway.sync = True
        accessible = self.homecontrol._gateway.online
        online_sync = self.homecontrol._gateway.sync
        self.homecontrol.updater._gateway_accessible(message={"properties": {"property.name": "gatewayAccessible",
                                                                             "property.value.new": {"accessible": False,
                                                                                                    "onlineSync": False}}})
        accessible_new = self.homecontrol._gateway.online
        online_sync_new = self.homecontrol._gateway.sync
        assert accessible != accessible_new
        assert online_sync != online_sync_new

    def test__meter(self):
        self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current = 5
        self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total = 230
        total = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        # Changing current value
        self.homecontrol.updater._meter(message={"properties": {"property.name": "currentValue",
                                                                "uid": f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                                "property.value.new": 7}})
        current_new = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current
        # Check if current value has changed
        assert current_new == 7
        # Check if total has not changed
        assert total == self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        # Changing total value
        self.homecontrol.updater._meter(message={"properties": {"property.name": "totalValue",
                                                                "uid": f"devolo.Meter:{self.devices.get('mains').get('uid')}",
                                                                "property.value.new": 235}})
        total_new = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").total
        # Check if total value has changed
        assert total_new == 235
        # Check if current value has not changed
        assert self.homecontrol.devices.get(self.devices.get('mains').get("uid")).consumption_property \
            .get(f"devolo.Meter:{self.devices.get('mains').get('uid')}").current == current_new

    def test__voltage_multi_level_sensor(self):
        self.homecontrol.devices.get(self.devices.get('mains').get("uid")).voltage_property \
            .get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current = 231
        current = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).voltage_property \
            .get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current
        self.homecontrol.updater._voltage_multi_level_sensor(message={"properties": {"uid": f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}",
                                                                                     "property.value.new": 234}})
        current_new = self.homecontrol.devices.get(self.devices.get('mains').get("uid")).voltage_property \
            .get(f"devolo.VoltageMultiLevelSensor:{self.devices.get('mains').get('uid')}").current

        assert current_new == 234
        assert current != current_new
