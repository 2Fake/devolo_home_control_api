import pytest
from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty


@pytest.mark.usefixtures("home_control_instance")
class TestConsumption:
    def test_consumption_property_invalid(self):
        with pytest.raises(WrongElementError):
            ConsumptionProperty(element_uid="invalid", setter=lambda uid, state: None)
