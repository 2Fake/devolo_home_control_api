import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.humidity_bar_property import HumidityBarProperty


@pytest.mark.usefixtures("home_control_instance")
class TestHumidityBar:
    def test_humidity_bar_property_invalid(self, connection):
        with pytest.raises(WrongElementError):
            HumidityBarProperty(connection=connection,
                                element_uid="invalid")
