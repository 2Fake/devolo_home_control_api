import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.consumption_property import ConsumptionProperty


@pytest.mark.usefixtures("home_control_instance")
class TestConsumption:
    def test_consumption_property_invalid(self, gateway_instance, mprm_session, mydevolo):
        with pytest.raises(WrongElementError):
            ConsumptionProperty(gateway=gateway_instance,
                                session=mprm_session,
                                mydevolo=mydevolo,
                                element_uid="invalid")
