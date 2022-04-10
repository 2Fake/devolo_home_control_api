import pytest
from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.multi_level_sensor_property import MultiLevelSensorProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMultiLevelSensorProperty:
    def test_multi_level_property_invalid(self):
        with pytest.raises(WrongElementError):
            MultiLevelSensorProperty(element_uid="invalid", setter=lambda uid, state: None)

    def test_unit(self):
        mlsp = MultiLevelSensorProperty(
            element_uid=self.devices.get("sensor").get("elementUIDs")[2],
            setter=lambda uid, state: None,
            sensor_type=self.devices.get("sensor").get("sensor_type"),
            value=self.devices.get("sensor").get("value"),
            unit=self.devices.get("sensor").get("unit"),
        )
        assert mlsp.unit == "%"
