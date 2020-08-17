"""Helper functions for splitting UID

Element UIDs and setting UIDs are the central identifies in devolo Home Control. However, for grouping information together
you often need to split them. This helper functions will do that for you.
"""

import re
from typing import Optional


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    return re.search(r".*?:(.*/\d{1,3})", element_uid).group(1)


def get_device_uid_from_setting_uid(setting_uid: str) -> str:
    """
    Return the device uid of the given setting UID.

    :param setting_uid: Setting UID, something like lis.hdm:ZWave:EB5A9F6C/2
    :return: Device UID, something like hdm:ZWave:EB5A9F6C/2
    """
    return re.search(r".*\.(.*/\d{1,3})", setting_uid).group(1)


def get_sub_device_uid_from_element_uid(element_uid: str) -> Optional[int]:
    """
    Return the sub device uid of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Sub device UID, something like 2
    """
    return None if "#" not in element_uid else int(element_uid.split("#")[-1])


def get_device_type_from_element_uid(element_uid: str) -> str:
    """
    Return the device type of the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device type, something like devolo.MultiLevelSensor
    """
    return element_uid.split(":")[0]
