import pytest

from devolo_home_control_api.properties.property import WrongElementError
from devolo_home_control_api.properties.voltage_property import VoltageProperty


@pytest.mark.usefixtures("home_control_instance")
@pytest.mark.usefixtures("mock_mprmrest__extract_data_from_element_uid")
class TestVoltageProperty:
    def test_voltage_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            VoltageProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid", current=0.0)
