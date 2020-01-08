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
        self._url = url
        self._uuid = None

    def get_gateway_serials(self) -> list:
        """
        Get Gateway serial number/s as a list
        :return: List of gateway serial numbers
        """
        gateways = []
        try:
            r = requests.get(self._url + "/v1/users/" + self._uuid + "/hc/gateways/status", auth=(self._user, self._password), timeout=60).json()['items']
            for gateway in r:
                gateways.append(gateway['gatewayId'])
        except IndexError:
            # TODO:
            pass
        return gateways

    def get_local_passkey(self, serial: str) -> str:
        """
        Get the local passkey of the given gateway for local authentication
        :param serial: gateway serial number
        :return: passkey for local authentication
        """
        local_passkey = None
        try:
            local_passkey = requests.get(self._url + "/v1/users/" + self.get_uuid() + "/hc/gateways/" + serial, auth=(self._user, self._password), timeout=60).json()['localPasskey']
        except IndexError:
            # TODO:
            pass
        return local_passkey

    def get_url(self) -> str:
        """
        Get the URL of the used stage
        :return: URL of used stage
        """
        return self._url

    def get_uuid(self) -> str:
        """
        Get the UUID of the current user
        :return: UUID of current user
        """
        if self._uuid is None:
            try:
                self._uuid = requests.get(self._url + "/v1/users/uuid", auth=(self._user, self._password), timeout=60).json()['uuid']
            except ConnectionError:
                # TODO:
                pass
        return self._uuid
