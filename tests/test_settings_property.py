import pytest

from devolo_home_control_api.properties.property import WrongElementError
from devolo_home_control_api.properties.settings_property import SettingsProperty


@pytest.mark.usefixtures("home_control_instance")
class TestSettingsProperty:
    def test_settings_property_valid(self, gateway_instance, mprm_session):
        setting_property = SettingsProperty(gateway=gateway_instance,
                                            session=mprm_session,
                                            element_uid=f"lis.{self.devices.get('mains').get('uid')}",
                                            led_setting=True,
                                            events_enabled=False,
                                            param_changed=True,
                                            local_switching=False,
                                            remote_switching=True,)
        assert setting_property.led_setting
        assert not setting_property.events_enabled
        assert setting_property.param_changed
        assert not setting_property.local_switching
        assert setting_property.remote_switching

    def test_settings_property_invalid(self, gateway_instance, mprm_session):
        with pytest.raises(WrongElementError):
            SettingsProperty(gateway=gateway_instance, session=mprm_session, element_uid="invalid")
