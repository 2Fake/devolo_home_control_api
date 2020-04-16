import pytest

import requests

from devolo_home_control_api.devices.zwave import Zwave, get_device_type_from_element_uid,\
    get_device_uid_from_element_uid, get_device_uid_from_setting_uid
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty

from .mocks.mock_gateway import MockGateway


@pytest.mark.usefixtures("mock_get_zwave_products")
class TestZwave:
    @pytest.mark.usefixtures("home_control_instance")
    @pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
    def test_get_property(self):
        device = Zwave(**self.devices.get("mains").get("properties"))
        gateway = MockGateway(self.gateway.get("id"))
        session = requests.Session()

        device.binary_switch_property = {}
        element_uid = f'devolo.BinarySwitch:{self.devices.get("mains").get("uid")}'
        device.binary_switch_property[element_uid] = \
            BinarySwitchProperty(gateway=gateway,
                                 session=session,
                                 element_uid=element_uid,
                                 state=self.devices.get("mains").get("properties").get("state"))

        assert isinstance(device.get_property("binary_switch")[0], BinarySwitchProperty)

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_property_invalid(self, mydevolo):
        device = Zwave(**self.devices.get("mains").get("properties"))

        with pytest.raises(AttributeError):
            device.get_property("binary_switch")

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_battery_level(self, mydevolo):
        # TODO: Use battery driven device
        device = Zwave(**self.devices.get("ambiguous_1"))

        assert device.batteryLevel == 55

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_device_online_state_state(self, mydevolo):
        device = Zwave(**self.devices.get("ambiguous_2"))
        assert device.status == 1

        device = Zwave(**self.devices.get("mains").get("properties"))
        assert device.status == 2

        device = Zwave(**self.devices.get("ambiguous_1"))
        assert device.status not in [1, 2]

    def test_get_device_type_from_element_uid(self):
        assert get_device_type_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "devolo.Meter"

    def test_get_device_uid_from_setting_uid(self):
        assert get_device_uid_from_setting_uid("lis.hdm:ZWave:EB5A9F6C/2") == "hdm:ZWave:EB5A9F6C/2"

    def test_get_device_uid_from_setting_uid_secure(self):
        assert get_device_uid_from_setting_uid("lis.hdm:ZWave:EB5A9F6C/2:secure") == "hdm:ZWave:EB5A9F6C/2"

    def test_get_device_uid_from_element_uid(self):
        assert get_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "hdm:ZWave:F6BF9812/2"

    def test_get_device_uid_from_element_uid_secure(self):
        assert get_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2:secure#2") == "hdm:ZWave:F6BF9812/2"

    def test_in_online_online(self, mydevolo):
        device = Zwave(**self.devices.get("mains").get("properties"))
        assert device.is_online()

    def test_in_online_offline(self, mydevolo):
        device = Zwave(**self.devices.get("offline"))
        assert not device.is_online()
