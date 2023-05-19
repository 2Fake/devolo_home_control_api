"""
Helper functions for splitting UID.

Element UIDs and setting UIDs are the central identifies in devolo Home Control. However, for grouping information together
you often need to split them. This helper functions will do that for you.
"""
from __future__ import annotations

import re


def get_device_uid_from_element_uid(element_uid: str) -> str:
    """
    Return device UID from the given element UID.

    :param element_uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
    :return: Device UID, something like hdm:ZWave:CBC56091/24
    """
    parts = re.search(r".*?:(.*/\d{1,3})", element_uid)
    if parts:
        return parts.group(1)
    raise ValueError("Element UID has a wrong format.")  # noqa: TRY003


def get_device_uid_from_setting_uid(setting_uid: str) -> str:
    """
    Return the device uid of the given setting UID.

    :param setting_uid: Setting UID, something like lis.hdm:ZWave:EB5A9F6C/2
    :return: Device UID, something like hdm:ZWave:EB5A9F6C/2
    """
    parts = re.search(r".*\.(.*/\d{1,3})", setting_uid)
    if parts:
        return parts.group(1)
    raise ValueError("Settings UID has a wrong format.")  # noqa: TRY003


def get_sub_device_uid_from_element_uid(element_uid: str) -> int | None:
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


def get_home_id_from_device_uid(device_uid: str) -> str:
    """
    Return the home id of the given device UID.

    :param device_uid: Device UID, something like hdm:ZWave:EB5A9F6C/4
    :return: Home ID, something like EB5A9F6C
    """
    parts = re.search(r":.*?(:)(.*)(/)", device_uid)
    if parts:
        return parts.group(2)
    raise ValueError("Device UID has a wrong format.")  # noqa: TRY003
