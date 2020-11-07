import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMultiLevelSensorProperty:
    def test_multi_level_property_invalid(self, connection):
        with pytest.raises(WrongElementError):
            MultiLevelSensorProperty(connection=connection,
                                     element_uid="invalid")

    def test_unit(self, connection):
        mlsp = MultiLevelSensorProperty(connection=connection,
                                        element_uid=self.devices.get("sensor").get("elementUIDs")[2],
                                        sensor_type=self.devices.get("sensor").get("sensor_type"),
                                        value=self.devices.get("sensor").get("value"),
                                        unit=self.devices.get("sensor").get("unit"))
        assert mlsp.unit == "%"
