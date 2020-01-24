import logging

import requests


class Mydevolo:
    """
    The Mydevolo object handles calls to the my devolo API v1 as singleton. It does not cover all API calls, just 
    those requested up to now. All calls are done in a user context, so you need to provide credentials of that user.

    We differentiate between general information like UUID or gateway IDs and information my devolo can provide, if 
    you know what you are looking for like gateway details. We treat the frommer as properties and the latter as
    parametries functions. Althouth they typically start with get, those are not getter function, as the result is
    not stored in the object.
    """
    __instance = None

    @staticmethod
    def get_instance():
        if Mydevolo.__instance == None:
            Mydevolo()
        return Mydevolo.__instance


    def __init__(self):
        if Mydevolo.__instance != None:
            raise SyntaxError("Please use Mydevolo.get_instance() to connect to my devolo.")
        else:
            self._logger = logging.getLogger(self.__class__.__name__)
            self._user = None
            self._password = None
            self._uuid = None
            self._gateway_ids = []

            self.url = "https://www.mydevolo.com"

            Mydevolo.__instance = self

    @property
    def user(self) -> str:
        """ The user (also known as my devolo ID) is used for basic authentication. """
        return self._user

    @user.setter
    def user(self, user: str):
        """ Invalidate uuid and gateway IDs on user name change. """
        self._user = user
        self._uuid = None
        self._gateway_ids == []

    @property
    def password(self) -> str:
        """ The password is used for basic authentication. """
        return self._password

    @password.setter
    def password(self, password: str):
        """ Invalidate uuid and gateway IDs on password change. """
        self._password = password
        self._uuid = None
        self._gateway_ids == []

    @property
    def uuid(self) -> str:
        """ The uuid is a central attribute in my devolo. Most URLs in the user context contain it. """
        if self._uuid == None:
            try:
                self._logger.debug("Getting UUID")
                self._uuid = self._call(self.url + "/v1/users/uuid").json().get("uuid")
            except KeyError:
                self._logger.error("Could not get UUID. Wrong Username or Password?")
                raise
            except requests.exceptions.ConnectionError:
                self._logger.error("Could not get UUID. Wrong URL used?")
                raise
        return self._uuid

    @property
    def gateway_ids(self) -> list:
        """ Get gateway IDs. """
        if self._gateway_ids == []:
            try:
                self._logger.debug(f"Getting list of gateways")
                items = self._call(self.url + "/v1/users/" + self.uuid + "/hc/gateways/status").json().get("items")
                for gateway in items:
                    self._gateway_ids.append(gateway.get("gatewayId"))
                    self._logger.debug(f"Adding {gateway['gatewayId']} to list of gateways.")
            except KeyError:
                self._logger.error("Could not get gateway list. Wrong Username or Password?")
                raise
            except requests.exceptions.ConnectionError:
                self._logger.error("Could not get gateway list. Wrong URL used?")
                raise
            if len(self._gateway_ids) == 0:
                self._logger.error("Could not get gateway list. No Gateway attached to account?")
                raise IndexError("No gateways")
        return self._gateway_ids


    def get_gateway(self, id: str) -> dict:
        """
        Get gateway details like name, local passkey and other.

        :param id: Gateway ID
        :return: Gateway object
        """
        try:
            self._logger.debug(f"Getting details for gateway {id}")
            details = self._call(self.url + "/v1/users/" + self.uuid + "/hc/gateways/" + id).json()
        except KeyError:
            self._logger.error("Could not get local passkey. Wrong Username or Password?")
            raise
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not get local passkey. Wrong URL used?")
            raise
        return details

    def get_full_url(self, id: str) -> str:
        """
        Get gateway's portal URL.

        :param id: Gateway ID
        :return: URL
        """
        try:
            self._logger.debug("Getting gateway")
            details = self._call(self.url + "/v1/users/" + self.uuid + "/hc/gateways/" + id + "/fullURL").json()
        except KeyError:
            self._logger.error("Could not get local passkey. Wrong Username or Password?")
            raise
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not get local passkey. Wrong URL used?")
            raise
        return details


    def _call(self, url: str) -> requests.Response:
        """
        Make a call to any entry point with the user's context.

        :param url: URL you want to call
        """
        headers = {'content-type': 'application/json'}
        return requests.get(url, auth=(self._user, self._password), headers=headers, timeout=60)
