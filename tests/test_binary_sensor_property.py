import pytest

from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty
from devolo_home_control_api.properties.property import WrongElementError


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySensorProperty:
    def test_binary_sensor_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            BinarySensorProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid", state=True)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_get_binary_sensor(self):
        assert self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
            .binary_sensor_property.get(self.devices.get("sensor").get("elementUIDs")[0]).state
