import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.binary_sensor_property import BinarySensorProperty


@pytest.mark.usefixtures("home_control_instance")
class TestBinarySensorProperty:

    def test_binary_sensor_property_invalid(self):
        with pytest.raises(WrongElementError):
            BinarySensorProperty(element_uid="invalid", state=True)

    def test_get_binary_sensor(self):
        assert self.homecontrol.devices.get(self.devices.get("sensor").get("uid")).binary_sensor_property.get(
            self.devices.get("sensor").get("elementUIDs")[0]).state
