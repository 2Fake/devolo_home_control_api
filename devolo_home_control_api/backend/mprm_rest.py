import json
import logging
import sys

from requests.exceptions import ReadTimeout

from ..exceptions.gateway import GatewayOfflineError
from ..mydevolo import Mydevolo


class MprmRest:
    """
    The abstract MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you have to create a derived class, that provides a Gateway object
    and a Session object.

    :param mydevolo_instance: Mydevolo instance for talking to the devolo Cloud
    """

    def __init__(self, mydevolo_instance: Mydevolo):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = mydevolo_instance
        self._data_id = 0
        self._local_ip = ""

    def get_all_devices(self) -> list:
        """
        Get all devices.

        :return: All devices and their properties.
        """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self.post(data)
        self._logger.debug(f"Response of 'get_all_devices':\n{response}")
        return response["result"]["items"][0]["properties"]["deviceUIDs"]

    def get_all_zones(self) -> dict:
        """
        Get all zones, also called rooms.

        :return: All zone IDs and their name.
        """
        self._logger.debug("Inspecting zones")
        data = {"method": "FIM/getFunctionalItems",
                "params": [["devolo.Grouping"], 0]}
        response = self.post(data)['result']['items'][0]['properties']['zones']
        self._logger.debug(f"Response of 'get_all_zones':\n{response}")
        return dict(zip([key["id"] for key in response], [key["name"] for key in response]))

    def get_data_from_uid_list(self, uids: list) -> list:
        """
        Returns data from an element UID list using an RPC call.

        :param uids: Element UIDs, something like [devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2,
                     devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#1]
        :return: Data connected to the element UIDs, payload so to say
        """
        data = {"method": "FIM/getFunctionalItems",
                "params": [uids, 0]}
        response = self.post(data)
        self._logger.debug(f"Response of 'get_data_from_uid_list':\n{response}")
        return response["result"]["items"]

    def get_name_and_element_uids(self, uid: str):
        """
        Returns the name, all element UIDs and the device model of the given device UID.

        :param uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self.post(data)
        self._logger.debug(f"Response of 'get_name_and_element_uids':\n{response}")
        return response["result"]["items"][0]["properties"]

    def post(self, data: dict) -> dict:
        """
        Communicate with the RPC interface. If the call times out, it is assumed that the gateway is offline and the state is
        changed accordingly.

        :param data: Data to be send
        :return: Response to the data
        """
        self._data_id += 1
        data['jsonrpc'] = "2.0"
        data['id'] = self._data_id
        try:
            response = self._session.post(self._session.url + "/remote/json-rpc",
                                          data=json.dumps(data),
                                          headers={"content-type": "application/json"},
                                          timeout=30).json()
        except ReadTimeout:
            self._logger.error("Gateway is offline.")
            self._logger.debug(sys.exc_info())
            self.gateway.update_state(False)
            raise GatewayOfflineError("Gateway is offline.") from None
        if response['id'] != data['id']:
            self._logger.error("Got an unexpected response after posting data.")
            self._logger.debug(f"Message had ID {data['id']}, response had ID {response['id']}.")
            raise ValueError("Got an unexpected response after posting data.")
        return response

    def refresh_session(self):
        """
        Refresh currently running session. Without this call from time to time especially websockets will terminate.
        """
        self._logger.debug("Refreshing session.")
        data = {"method": "FIM/invokeOperation",
                "params": [f"devolo.UserPrefs.{self._mydevolo.uuid()}", "resetSessionTimeout", []]}
        self.post(data)
