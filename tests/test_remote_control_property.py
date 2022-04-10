import pytest
from devolo_home_control_api.exceptions.device import WrongElementError
from devolo_home_control_api.properties.remote_control_property import RemoteControlProperty


@pytest.mark.usefixtures("home_control_instance")
class TestRemoteControlProperty:
    def test_remote_control_property_invalid(self):
        with pytest.raises(WrongElementError):
            RemoteControlProperty(element_uid="invalid", setter=lambda uid, state: None)

    def test_set_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("remote").get("uid")).remote_control_property.get(
                self.devices.get("remote").get("elementUIDs")[0]
            ).set(5)

    def test_set_valid(self):
        self.homecontrol.devices.get(self.devices.get("remote").get("uid")).remote_control_property.get(
            self.devices.get("remote").get("elementUIDs")[0]
        ).set(1)
        assert (
            self.homecontrol.devices.get(self.devices.get("remote").get("uid"))
            .remote_control_property.get(self.devices.get("remote").get("elementUIDs")[0])
            .key_pressed
        )
