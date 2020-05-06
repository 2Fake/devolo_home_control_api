import pytest

from devolo_home_control_api.exceptions.device import WrongElementError
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

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_gds_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("general_device_settings").set(events_enabled=False)
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("general_device_settings").events_enabled

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_lis_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("led").set(led_setting=False)
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("led").led_setting

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_mss_invalid(self):
        with pytest.raises(ValueError):
            self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
                .settings_property.get("motion_sensitivity").set(motion_sensitivity=110)

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_mss_valid(self):
        self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
            .settings_property.get("motion_sensitivity").set(motion_sensitivity=90)
        assert self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
            .settings_property.get("motion_sensitivity").motion_sensitivity == 90

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_ps_valid(self):
        self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("protection").set(local_switching=False)
        assert not self.homecontrol.devices.get(self.devices.get("mains").get("uid"))\
            .settings_property.get("protection").local_switching

    @pytest.mark.usefixtures("mock_mprmrest__post_set")
    def test__set_trs_valid(self):
        self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
            .settings_property.get("temperature_report").set(temp_report=False)
        assert not self.homecontrol.devices.get(self.devices.get("sensor").get("uid"))\
            .settings_property.get("temperature_report").temp_report
