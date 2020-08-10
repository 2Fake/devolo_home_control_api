import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.remote_control_property import RemoteControlProperty


@pytest.mark.usefixtures("home_control_instance")
class TestRemoteControlProperty:
    def test_remote_control_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            RemoteControlProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid", key_pressed=1)

    def test_set_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("remote").get("uid"))\
                .remote_control_property.get(self.devices.get("remote").get("elementUIDs")[0]).set(5)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test_set_valid(self):
        self.homecontrol.devices.get(self.devices.get("remote").get("uid"))\
            .remote_control_property.get(self.devices.get("remote").get("elementUIDs")[0]).set(1)
        assert self.homecontrol.devices.get(self.devices.get("remote").get("uid"))\
            .remote_control_property.get(self.devices.get("remote").get("elementUIDs")[0]).key_pressed
