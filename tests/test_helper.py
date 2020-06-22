from devolo_home_control_api.helper.string import camel_case_to_snake_case
from devolo_home_control_api.helper.uid import (
    get_device_type_from_element_uid, get_device_uid_from_element_uid,
    get_device_uid_from_setting_uid, get_sub_device_uid_from_element_uid)


class TestHelper:
    def test_camel_case_to_snake_case(self):
        assert camel_case_to_snake_case("CamelCase") == "camel_case"
        assert camel_case_to_snake_case("camelCase") == "camel_case"

    def test_get_device_type_from_element_uid(self):
        assert get_device_type_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "devolo.Meter"

    def test_get_device_uid_from_element_uid(self):
        assert get_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == "hdm:ZWave:F6BF9812/2"

    def test_get_device_uid_from_element_uid_secure(self):
        assert get_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2:secure#2") == "hdm:ZWave:F6BF9812/2"

    def test_get_device_uid_from_setting_uid(self):
        assert get_device_uid_from_setting_uid("lis.hdm:ZWave:EB5A9F6C/2") == "hdm:ZWave:EB5A9F6C/2"

    def test_get_device_uid_from_setting_uid_secure(self):
        assert get_device_uid_from_setting_uid("lis.hdm:ZWave:EB5A9F6C/2:secure") == "hdm:ZWave:EB5A9F6C/2"

    def test_get_sub_device_uid_from_element_uid(self):
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2#2") == 2
        assert get_sub_device_uid_from_element_uid("devolo.Meter:hdm:ZWave:F6BF9812/2") is None
