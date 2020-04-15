import pytest

from devolo_home_control_api.properties.dewpoint_sensor_property import DewpointSensorProperty
from devolo_home_control_api.properties.property import WrongElementError


@pytest.mark.usefixtures("home_control_instance")
class TestDewpointSensor:
    def test_dewpoint_sensor_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            DewpointSensorProperty(gateway=gateway_instance,
                                   session=mprm_session,
                                   element_uid="invalid",
                                   value=18)
