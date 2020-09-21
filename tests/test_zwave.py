import pytest

import requests

from devolo_home_control_api.devices.zwave import Zwave
from devolo_home_control_api.properties.binary_switch_property import BinarySwitchProperty

from .mocks.mock_gateway import MockGateway


class TestZwave:
    @pytest.mark.usefixtures("home_control_instance")
    @pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_get_property(self):
        device = Zwave(**self.devices['mains']['properties'])
        gateway = MockGateway(self.gateway['id'])
        session = requests.Session()

        device.binary_switch_property = {}
        element_uid = f"devolo.BinarySwitch:{self.devices['mains']['uid']}"
        device.binary_switch_property[element_uid] = \
            BinarySwitchProperty(gateway=gateway,
                                 session=session,
                                 element_uid=element_uid,
                                 state=self.devices['mains']['properties']['state'],
                                 enabled=self.devices['mains']['properties']['guiEnabled'])

        assert isinstance(device.get_property("binary_switch")[0], BinarySwitchProperty)

    @pytest.mark.usefixtures("mock_mydevolo__call")
    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_get_property_invalid(self, mydevolo):
        device = Zwave(**self.devices['mains']['properties'])
        with pytest.raises(AttributeError):
            device.get_property("binary_switch")

    @pytest.mark.usefixtures("mock_mydevolo__call")
    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_battery_level(self, mydevolo):
        device = Zwave(**self.devices['remote'])
        assert device.battery_level == self.devices['remote']['batteryLevel']

    @pytest.mark.usefixtures("mock_mydevolo__call")
    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_device_online_state_state(self, mydevolo):
        device = Zwave(**self.devices['ambiguous_2'])
        assert device.status == 1

        device = Zwave(**self.devices['mains']['properties'])
        assert device.status == 2

        device = Zwave(**self.devices['ambiguous_1'])
        assert device.status not in [1, 2]

    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_in_online_online(self, mydevolo):
        device = Zwave(**self.devices['mains']['properties'])
        assert device.is_online()

    @pytest.mark.usefixtures("mock_get_zwave_products")
    def test_in_online_offline(self, mydevolo):
        device = Zwave(**self.devices['offline'])
        assert not device.is_online()

    @pytest.mark.usefixtures("mock_mydevolo__call")
    def test_get_zwave_info(self, mydevolo):
        device = Zwave(**self.devices['mains']['properties'])
        device.get_zwave_info()
        assert device.brand == self.devices['mains']['brand']
