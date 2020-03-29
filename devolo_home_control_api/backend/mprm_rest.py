import json
import logging

from requests import ReadTimeout

from ..mydevolo import Mydevolo


class MprmRest:
    """
    The abstract MprmRest object handles calls to the so called mPRM. It does not cover all API calls, just those requested
    up to now. All calls are done in a gateway context, so you have to create a derived class, that provides a Gateway object
    and a Session object.
    """

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mydevolo = Mydevolo.get_instance()
        self._data_id = 0
        self._local_ip = None


    def get_all_devices(self) -> list:
        """
        Get all devices.

        :return: All devices and their properties.
        """
        self._logger.info("Inspecting devices")
        data = {"method": "FIM/getFunctionalItems",
                "params": [['devolo.DevicesPage'], 0]}
        response = self.post(data)
        return response.get("result").get("items")[0].get("properties").get("deviceUIDs")

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
        return response.get("result").get("items")

    def get_name_and_element_uids(self, uid: str):
        """
        Returns the name, all element UIDs and the device model of the given device UID.

        :param uid: Element UID, something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        """
        data = {"method": "FIM/getFunctionalItems",
                "params": [[uid], 0]}
        response = self.post(data)
        properties = response.get("result").get("items")[0].get("properties")
        return properties

    def post(self, data: dict) -> dict:
        """
        Communicate with the RPC interface.

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
            self._gateway.update_state(False)
            raise MprmDeviceCommunicationError("Gateway is offline.") from None
        if response['id'] != data['id']:
            self._logger.error("Got an unexpected response after posting data.")
            raise ValueError("Got an unexpected response after posting data.")
        return response


class MprmDeviceCommunicationError(Exception):
    """ Communicating to a device via mPRM failed """


class MprmDeviceNotFoundError(Exception):
    """ A device like this was not found """
