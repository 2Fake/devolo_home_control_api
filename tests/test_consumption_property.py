import pytest

from devolo_home_control_api.properties.consumption_property import ConsumptionProperty
from devolo_home_control_api.properties.property import WrongElementError


@pytest.mark.usefixtures("home_control_instance")
class TestConsumption:
    def test_consumption_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            ConsumptionProperty(gateway=gateway_instance,
                                session=mprm_session,
                                element_uid="invalid",
                                current=0.0,
                                total=0.0,
                                total_since=1231412412)
