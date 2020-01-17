import logging

import requests


class Mydevolo:

    def __init__(self, user: str, password: str, url: str = 'https://www.mydevolo.com'):
        """
        Constructor
        :param user: devolo ID
        :param password: password
        :param url: URL of the stage
        """
        self._user = user
        self._password = password

        self._logger = logging.getLogger(self.__class__.__name__)

        self.url = url
        self.uuid = self._get_uuid()

    def get_gateway_serials(self) -> list:
        """
        Get Gateway serial number/s as a list
        :return: List of gateway serial numbers
        """
        gateways = []
        try:
            r = requests.get(self.url + '/v1/users/' + self.uuid + '/hc/gateways/status', auth=(self._user, self._password), timeout=60).json()['items']
            self._logger.debug(f"Getting list of gateways")
            for gateway in r:
                gateways.append(gateway['gatewayId'])
                self._logger.debug(f"Adding {gateway['gatewayId']} to list of gateways.")
        except KeyError:
            self._logger.error("Could not get gateway list. Wrong Username or Password?")
            raise
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not get gateway list. Wrong URL used?")
            raise
        if len(gateways) == 0:
            self._logger.error("Could not get gateway list. No Gateway attached to account?")
            raise IndexError("No gateways")
        return gateways

    def get_local_passkey(self, serial: str) -> str:
        """
        Get the local passkey of the given gateway for local authentication
        :param serial: gateway serial number
        :return: passkey for local authentication
        """
        local_passkey = None
        try:
            local_passkey = requests.get(self.url + '/v1/users/' + self.uuid + '/hc/gateways/' + serial, auth=(self._user, self._password), timeout=60).json()['localPasskey']
            self._logger.debug("Getting local passkey")
        except KeyError:
            self._logger.error("Could not get local passkey. Wrong Username or Password?")
            raise
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not get local passkey. Wrong URL used?")
            raise
        return local_passkey

    def _get_uuid(self) -> str:
        """
        Get the UUID of the current user
        :return: UUID of current user
        """
        try:
            uuid = requests.get(self.url + '/v1/users/uuid', auth=(self._user, self._password), timeout=60).json()['uuid']
            self._logger.debug("Getting UUID")
        except KeyError:
            self._logger.error("Could not get UUID. Wrong Username or Password?")
            raise
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not get UUID. Wrong URL used?")
            raise
        return uuid
