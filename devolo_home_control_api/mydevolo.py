import logging

import requests


class Mydevolo:
    """
    The Mydevolo object handles calls to the my devolo API v1 as singleton. It does not cover all API calls, just
    those requested up to now. All calls are done in a user context, so you need to provide credentials of that user.

    We differentiate between general information like UUID or gateway IDs and information my devolo can provide, if
    you know what you are looking for like gateway details. We treat the frommer as properties and the latter as
    parametriesed functions. Althouth they typically start with get, those are not getter function, as the result is
    not stored in the object.
    """

    __instance = None

    @staticmethod
    def get_instance():
        if Mydevolo.__instance is None:
            Mydevolo()
        return Mydevolo.__instance

    @staticmethod
    def del_instance():
        Mydevolo.__instance = None


    def __init__(self):
        if Mydevolo.__instance is not None:
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
        self._gateway_ids = []

    @property
    def password(self) -> str:
        """ The password is used for basic authentication. """
        return self._password

    @password.setter
    def password(self, password: str):
        """ Invalidate uuid and gateway IDs on password change. """
        self._password = password
        self._uuid = None
        self._gateway_ids = []

    @property
    def uuid(self) -> str:
        """ The uuid is a central attribute in my devolo. Most URLs in the user context contain it. """
        if self._uuid is None:
            self._logger.debug("Getting UUID")
            self._uuid = self._call(self.url + "/v1/users/uuid").get("uuid")
        return self._uuid

    @property
    def maintenance(self) -> bool:
        """ If devolo Home Control is in maintenance, there is not much we can do via cloud. """
        state = self._call(self.url + "/v1/hc/maintenance").get("state")
        if state == "on":
            return False
        else:
            self._logger.warning("devolo Home Control is in maintenance mode.")
            return True

    @property
    def gateway_ids(self) -> list:
        """ Get gateway IDs. """
        if not self._gateway_ids:
            self._logger.debug(f"Getting list of gateways")
            items = self._call(self.url + "/v1/users/" + self.uuid + "/hc/gateways/status").get("items")
            for gateway in items:
                self._gateway_ids.append(gateway.get("gatewayId"))
                self._logger.debug(f'Adding {gateway.get("gatewayId")} to list of gateways.')
            if len(self._gateway_ids) == 0:
                self._logger.error("Could not get gateway list. No Gateway attached to account?")
                raise IndexError("No gateways")
        return self._gateway_ids


    def get_gateway(self, gateway_id: str) -> dict:
        """
        Get gateway details like name, local passkey and other.

        :param gateway_id: Gateway ID
        :return: Gateway object
        """
        self._logger.debug(f"Getting details for gateway {gateway_id}")
        return self._call(self.url + "/v1/users/" + self.uuid + "/hc/gateways/" + gateway_id)

    def get_full_url(self, gateway_id: str) -> str:
        """
        Get gateway's portal URL.

        :param gateway_id: Gateway ID
        :return: URL
        """
        self._logger.debug("Getting full URL of gateway.")
        return self._call(self.url + "/v1/users/"
                          + self.uuid + "/hc/gateways/" + gateway_id + "/fullURL").get("url")


    def _call(self, url: str) -> dict:
        """
        Make a call to any entry point with the user's context.
        """
        responds = requests.get(url,
                                auth=(self._user, self._password),
                                headers={'content-type': 'application/json'},
                                timeout=60)
        if responds.status_code == requests.codes.forbidden:
            self._logger.error("Could not get full URL. Wrong username or password?")
            raise WrongCredentialsError("Wrong username or password.")
        elif responds.status_code == requests.codes.not_found:
            self._logger.error("Could not get full URL. Wrong gateway ID used?")
            raise WrongUrlError(f"Wrong URL: {url}")
        return responds.json()


class WrongCredentialsError(Exception):
    """ Wrong credentials were used. """


class WrongUrlError(Exception):
    """ Wrong URL was used. """
