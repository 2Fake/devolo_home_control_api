"""Helper functions for splitting UID."""
from devolo_home_control_api.helper.uid import (
    get_device_type_from_element_uid,
    get_device_uid_from_element_uid,
    get_device_uid_from_setting_uid,
    get_home_id_from_device_uid,
    get_sub_device_uid_from_element_uid,
)

DEVICE_UID = "hdm:ZWave:CBC56091/24"
ELEMENT_UID = "devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2"
SETTING_UID = "lis.hdm:ZWave:CBC56091/24"


def test_device_uid_from_element_uid() -> None:
    """Test getting the device uid from an element uid."""
    assert get_device_uid_from_element_uid(ELEMENT_UID) == DEVICE_UID


def test_device_uid_from_setting_uid() -> None:
    """Test getting the device uid from a setting uid."""
    assert get_device_uid_from_setting_uid(SETTING_UID) == DEVICE_UID


def test_sub_device_uid_from_element_uid() -> None:
    """Test getting the sub device uid from an element uid."""
    assert get_sub_device_uid_from_element_uid(ELEMENT_UID) == 2


def test_device_type_from_element_uid() -> None:
    """Test getting the device type from an element uid."""
    assert get_device_type_from_element_uid(ELEMENT_UID) == "devolo.MultiLevelSensor"


def test_home_id_from_device_uid() -> None:
    """Test getting the home ID from a device UID."""
    assert get_home_id_from_device_uid(DEVICE_UID) == "CBC56091"
