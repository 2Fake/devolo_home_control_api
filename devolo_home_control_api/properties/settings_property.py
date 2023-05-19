"""Settings."""
from __future__ import annotations

from datetime import tzinfo
from enum import IntEnum
from typing import Any, Callable

from devolo_home_control_api.exceptions import WrongElementError

from .property import Property


class SettingsProperty(Property):
    """
    Object for settings. Basically, everything can be stored in here as long as there is a corresponding functional item on
    the gateway. This is to be as flexible to gateway firmware changes as possible. So if new attributes appear or old ones
    are removed, they should be handled at least in reading them. Nevertheless, a few unwanted attributes are filtered.

    :param element_uid: Element UID, something like acs.hdm:ZWave:CBC56091/24
    :param tz: Timezone the last activity is recorded in
    :param setter: Method to call on setting the state
    :param **kwargs: Any setting, that shall be available in this object
    """

    calibration_status: bool
    direction: bool
    events_enabled: bool
    icon: str
    inverted: int
    led_setting: bool
    local_switching: bool
    motion_sensitivity: int
    name: str
    param_changed: bool
    remote_switching: bool
    temp_report: bool
    tone: int
    value: bool
    zone_id: str

    def __init__(self, element_uid: str, tz: tzinfo, setter: Callable[..., bool], **kwargs: Any) -> None:
        """Initialize the setting."""
        if not element_uid.startswith(
            ("acs", "bas", "bss", "cps", "gds", "lis", "mas", "mss", "ps", "sts", "stmss", "trs", "vfs")
        ):
            raise WrongElementError(element_uid, self.__class__.__name__)

        super().__init__(element_uid, tz)
        self._setter = setter

        if element_uid.startswith("gds") and {"zones", "zone_id"} <= kwargs.keys():
            self.zone = kwargs.pop("zones")[kwargs["zone_id"]]

        for key, value in kwargs.items():
            setattr(self, key, value)

        setter_method: dict[str, Callable[..., bool]] = {
            "bas": self._set_bas,
            "gds": self._set_gds,
            "lis": self._set_lis,
            "mss": self._set_mss,
            "ps": self._set_ps,
            "trs": self._set_trs,
            "vfs": self._set_lis,
        }

        # Depending on the type of setting property, this will create a callable named "set".
        # However, this methods are not working, if the gateway is connected locally, yet.
        self.set = setter_method.get(element_uid.split(".")[0], lambda: False)

        # Clean up attributes which are unwanted.
        clean_up_list = ["device_uid"]

        for attribute in clean_up_list:
            delattr(self, attribute)

    def _set_bas(self, value: bool) -> bool:
        """
        Set a binary async setting. This is e.g. the muted setting of a siren or the three way switch setting of a dimmer.

        :param value: New state
        """
        if self._setter(self.element_uid, [value]):
            self.value = value
            self._logger.debug("Binary async setting property %s set to %s", self.element_uid, value)
            return True
        return False

    def _set_gds(self, **kwargs: Any) -> bool:
        """
        Set one or more general device setting.

        :key events_enabled: Show events in diary
        :type events_enabled: bool
        :key icon: New icon name
        :type icon: str
        :key name: New device name
        :type name: str
        :key zone_id: New zone_id (ATTENTION: This is NOT the name of the location)
        :type zone_id: str
        """
        events_enabled: bool = kwargs.pop("events_enabled", self.events_enabled)
        icon: str = kwargs.pop("icon", self.icon)
        name: str = kwargs.pop("name", self.name)
        zone_id: str = kwargs.pop("zone_id", self.zone_id)

        settings = {
            "events_enabled": events_enabled,
            "icon": icon,
            "name": name,
            "zone_id": zone_id,
        }
        if self._setter(self.element_uid, [settings]):
            self.events_enabled = events_enabled
            self.icon = icon
            self.name = name
            self.zone_id = zone_id
            self._logger.debug("General device setting %s changed.", self.element_uid)
            return True
        return False

    def _set_lis(self, led_setting: bool) -> bool:
        """
        Set led settings.

        :param led_setting: LED indication setting
        """
        if self._setter(self.element_uid, [led_setting]):
            self.led_setting = led_setting
            self._logger.debug("LED indication setting property %s set to %s", self.element_uid, led_setting)
            return True
        return False

    def _set_mss(self, motion_sensitivity: int) -> bool:
        """
        Set motion sensitivity.

        :param motion_sensitivity: Integer for the motion sensitivity setting.
        """
        if not MotionSensitivity.MIN <= motion_sensitivity <= MotionSensitivity.MAX:
            raise ValueError(f"Value must be between {MotionSensitivity.MIN} and {MotionSensitivity.MAX}")  # noqa: TRY003
        if self._setter(self.element_uid, [motion_sensitivity]):
            self.motion_sensitivity = motion_sensitivity
            self._logger.debug("Motion sensitivity setting property %s set to %s", self.element_uid, motion_sensitivity)
            return True
        return False

    def _set_ps(self, **kwargs: bool) -> bool:
        """
        Set one or both protection settings.

        :key local_switching: Allow local switching
        :type local_switching: bool
        :key remote_switching: Allow local switching
        :type remote_switching: bool
        """
        local_switching = kwargs.pop("local_switching", self.local_switching)
        remote_switching = kwargs.pop("remote_switching", self.remote_switching)

        if self._setter(
            self.element_uid,
            [
                {
                    "localSwitch": local_switching,
                    "remoteSwitch": remote_switching,
                }
            ],
        ):
            self.local_switching = local_switching
            self.remote_switching = remote_switching
            self._logger.debug(
                "Protection setting property %s set to %s (local) and %s (remote).",
                self.element_uid,
                local_switching,
                remote_switching,
            )
            return True
        return False

    def _set_trs(self, temp_report: bool) -> bool:
        """
        Set temperature report setting.

        :param temp_report: Boolean of the target value
        """
        if self._setter(self.element_uid, [temp_report]):
            self.temp_report = temp_report
            self._logger.debug("Temperature report setting property %s set to %s", self.element_uid, temp_report)
            return True
        return False


class MotionSensitivity(IntEnum):
    """Motion sensitivity boundary value."""

    MIN = 0
    MAX = 100
