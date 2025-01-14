"""mPRM communication via REST."""
from __future__ import annotations

import json
import logging
import sys
from abc import ABC
from enum import IntEnum
from typing import Any

from requests import Session
from requests.exceptions import ConnectionError, ReadTimeout  # noqa: A004

from devolo_home_control_api.devices import Gateway
from devolo_home_control_api.exceptions import GatewayOfflineError
from devolo_home_control_api.mydevolo import Mydevolo


class MprmRest(ABC):
    """
    The abstract MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you have to create a derived class, that provides a Gateway object
    and a Session object.
    """

    def __init__(self) -> None:
        """Initialize REST communication."""
        logging.captureWarnings(capture=True)

        self._logger = logging.getLogger(self.__class__.__name__)
        self._data_id = 0
        self._local_ip = ""
        self._url = ""

        self._mydevolo: Mydevolo
        self._session: Session
        self.gateway: Gateway

    def get_all_devices(self) -> list[str]:
        """
        Get all devices.

        :return: All devices and their properties.
        """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems", "params": [["devolo.DevicesPage"], 0]}
        response = self._post(data)
        self._logger.debug("Response of 'get_all_devices':\n%s", response)
        return response["result"]["items"][0]["properties"]["deviceUIDs"]

    def get_all_zones(self) -> dict[str, str]:
        """
        Get all zones, also called rooms.

        :return: All zone IDs and their name.
        """
        self._logger.debug("Inspecting zones")
        data = {"method": "FIM/getFunctionalItems", "params": [["devolo.Grouping"], 0]}
        response = self._post(data)["result"]["items"][0]["properties"]["zones"]
        self._logger.debug("Response of 'get_all_zones':\n%s", response)
        return {key["id"]: key["name"] for key in response}

    def get_data_from_uid_list(self, uids: list[str]) -> list[dict[str, Any]]:
        """
        Return data from an element UID list using an RPC call.

        :param uids: Element UIDs, something like [devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2,
                     devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#1]
        :return: Data connected to the element UIDs, payload so to say
        """
        data = {"method": "FIM/getFunctionalItems", "params": [uids, 0]}
        response = self._post(data)
        self._logger.debug("Response of 'get_data_from_uid_list':\n%s", response)
        return response["result"]["items"]

    def refresh_session(self) -> None:
        """Refresh currently running session. Without this call from time to time especially websockets will terminate."""
        self._logger.debug("Refreshing session.")
        data = {
            "method": "FIM/invokeOperation",
            "params": [f"devolo.UserPrefs.{self._mydevolo.uuid()}", "resetSessionTimeout", []],
        }
        self._post(data)

    def set_binary_switch(self, uid: str, state: bool) -> bool:
        """
        Set a binary switch state of a device.

        :param uid: Element UID, something like devolo.BinarySwitch:hdm:ZWave:CBC56091/24
        :param state: True if switching on, False if switching off
        :return: True if successfully switched, false otherwise
        """
        data: dict[str, str | list] = {"method": "FIM/invokeOperation", "params": [uid, "turnOn" if state else "turnOff", []]}
        response = self._post(data)
        return self._evaluate_response(uid=uid, value=state, response=response)

    def set_multi_level_switch(self, uid: str, value: float) -> bool:
        """
        Set a multi level switch value of a device.

        :param uid: Element UID, something like devolo.Dimmer:hdm:ZWave:CBC56091/24
        :param value: Value the multi level switch shall have
        :return: True if successfully switched, false otherwise
        """
        data = {"method": "FIM/invokeOperation", "params": [uid, "sendValue", [value]]}
        response = self._post(data)
        return self._evaluate_response(uid=uid, value=value, response=response)

    def set_remote_control(self, uid: str, key_pressed: int) -> bool:
        """
        Press the button of a remote control virtually.

        :param uid: Element UID, something like devolo.RemoteControl:hdm:ZWave:CBC56091/24
        :param key_pressed: Number of the button pressed
        :return: True if successfully switched, false otherwise
        """
        data = {"method": "FIM/invokeOperation", "params": [uid, "pressKey", [key_pressed]]}
        response = self._post(data)
        return self._evaluate_response(uid=uid, value=key_pressed, response=response)

    def set_setting(self, uid: str, setting: list[str]) -> bool:
        """
        Set a setting of a device.

        :param uid: Element UID, something like acs.hdm:ZWave:CBC56091/24
        :param setting: Settings to set
        :return: True if successfully switched, false otherwise
        """
        data = {"method": "FIM/invokeOperation", "params": [uid, "save", setting]}
        response = self._post(data)
        return self._evaluate_response(uid=uid, value=setting, response=response)

    def _evaluate_response(self, uid: str, value: bool | float | list[str], response: dict[str, Any]) -> bool:
        """Evaluate the response of setting a device to a value."""
        if response["result"].get("status") == RestResponseStatus.VALID:
            return True
        if response["result"].get("status") == RestResponseStatus.INVALID:
            self._logger.debug("Value of %s is already %s.", uid, value)
        else:
            self._logger.error("Something went wrong setting %s.", uid)
            self._logger.debug("Response to set command:\n%s", response)
        return False

    def _post(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Communicate with the RPC interface. If the call times out, it is assumed that the gateway is offline and the state is
        changed accordingly.

        :param data: Data to be send
        :return: Response to the data
        """
        self._data_id += 1
        data["jsonrpc"] = "2.0"
        data["id"] = self._data_id
        try:
            response = self._session.post(
                f"{self._url}/remote/json-rpc", data=json.dumps(data), headers={"content-type": "application/json"}, timeout=30
            ).json()

        except (ConnectionError, ReadTimeout):
            self._logger.error("Gateway is offline.")
            self._logger.debug(sys.exc_info())
            self.gateway.update_state(online=False)
            raise GatewayOfflineError from None
        if response["id"] != data["id"]:
            self._logger.error("Got an unexpected response after posting data.")
            self._logger.debug("Message had ID %s, response had ID %s.", data["id"], response["id"])
            raise ValueError("Got an unexpected response after posting data.")  # noqa: TRY003
        return response


class RestResponseStatus(IntEnum):
    """Status codes for mPRM responses."""

    VALID = 1
    INVALID = 2
