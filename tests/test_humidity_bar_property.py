import pytest

from devolo_home_control_api.properties.humidity_bar_property import HumidityBarProperty
from devolo_home_control_api.properties.property import WrongElementError


@pytest.mark.usefixtures("home_control_instance")
class TestHumidityBar:
    def test_humidity_bar_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            HumidityBarProperty(gateway=gateway_instance,
                                session=mprm_session,
                                element_uid="invalid",
                                value=75,
                                zone=1)
