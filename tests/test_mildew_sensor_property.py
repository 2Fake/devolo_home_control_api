import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.mildew_sensor_property import MildewSensorProperty


@pytest.mark.usefixtures("home_control_instance")
class TestMildewSensor:
    def test_mildew_sensor_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            MildewSensorProperty(gateway=gateway_instance,
                                 session=mprm_session,
                                 element_uid="invalid",
                                 state=False)
