import logging

import requests

from . import __version__
from .exceptions.gateway import GatewayOfflineError
from .exceptions.general import WrongCredentialsError, WrongUrlError


class Mydevolo:
    """
    The Mydevolo object handles calls to the my devolo API v1. It does not cover all API calls, just those requested up to now.
    All calls are done in a user context, so you need to provide credentials of that user.
    """

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._user = None
        self._password = None
        self._uuid = None
        self._gateway_ids = []

        self.url = "https://www.mydevolo.com"

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

    def credentials_valid(self) -> bool:
        """
        Check if current credentials are valid. This is done by trying to get the UUID. If that fails, credentials must be
        wrong. If it succeeds, we can reuse the UUID for later usages.
        """
        try:
            self.uuid()
            return True
        except WrongCredentialsError:
            return False

    def get_gateway_ids(self) -> list:
        """
        Get all gateway IDs attached to current account.
        """
        if not self._gateway_ids:
            self._logger.debug("Getting list of gateways")
            items = self._call(f"{self.url}/v1/users/{self.uuid()}/hc/gateways/status")['items']
            for gateway in items:
                self._gateway_ids.append(gateway.get("gatewayId"))
                self._logger.debug("Adding %s to list of gateways.", gateway.get("gatewayId"))
            if len(self._gateway_ids) == 0:
                self._logger.error("Could not get gateway list. No gateway attached to account?")
                raise IndexError("No gateways found.")
        return self._gateway_ids

    def get_gateway(self, gateway_id: str) -> dict:
        """
        Get gateway details like name, local passkey and other.

        :param gateway_id: Gateway ID
        :return: Gateway details
        """
        self._logger.debug("Getting details for gateway %s", gateway_id)
        try:
            details = self._call(f"{self.url}/v1/users/{self.uuid()}/hc/gateways/{gateway_id}")
        except WrongUrlError:
            self._logger.error("Could not get full URL. Wrong gateway ID used?")
            raise
        return details

    def get_full_url(self, gateway_id: str) -> str:
        """
        Get gateway's portal URL.

        :param gateway_id: Gateway ID
        :return: URL to access the gateway's portal.
        """
        self._logger.debug("Getting full URL of gateway.")
        return self._call(f"{self.url}/v1/users/{self.uuid()}/hc/gateways/{gateway_id}/fullURL")['url']

    def get_zwave_products(self, manufacturer: str, product_type: str, product: str) -> dict:
        """
        Get information about a Z-Wave device.

        :param manufacturer: The manufacturer ID in hex.
        :param product_type: The product type ID in hex.
        :param product: The product ID in hex.
        :return: All known product information.
        """
        self._logger.debug("Getting information for %s/%s/%s", manufacturer, product_type, product)
        try:
            device_info = self._call(f"{self.url}/v1/zwave/products/{manufacturer}/{product_type}/{product}")
        except WrongUrlError:
            # At some devices no device information are returned
            self._logger.debug("No device info found")
            device_info = {
                "brand": "devolo" if manufacturer == "0x0175" else "Unknown",
                "deviceType": "Unknown",
                "genericDeviceClass": "Unknown",
                "href": f"{self.url}/v1/zwave/products/{manufacturer}/{product_type}/{product}",
                "identifier": "Unknown",
                "isZWavePlus": False,
                "manufacturerId": manufacturer,
                "name": "Unknown",
                "productId": product,
                "productTypeId": product_type,
                "specificDeviceClass": "Unknown",
                "zwaveVersion": "Unknown",
            }
        return device_info

    def maintenance(self) -> bool:
        """
        If devolo Home Control is in maintenance, there is not much we can do via cloud.
        """
        state = self._call(f"{self.url}/v1/hc/maintenance")['state']
        if state == "on":
            return False
        self._logger.warning("devolo Home Control is in maintenance mode.")
        return True

    def uuid(self) -> str:
        """
        The uuid is a central attribute in my devolo. Most URLs in the user's context contain it.
        """
        if self._uuid is None:
            self._logger.debug("Getting UUID")
            self._uuid = self._call(f"{self.url.rstrip('/')}/v1/users/uuid")['uuid']
        return self._uuid

    def _call(self, url: str) -> dict:
        """ Make a call to any entry point with the user's context. """
        headers = {
            "content-type": "application/json",
            "User-Agent": f"devolo_home_control_api/{__version__}"
        }
        responds = requests.get(url, auth=(self._user, self._password), headers=headers, timeout=60)

        if responds.status_code == requests.codes.forbidden:  # pylint: disable=no-member
            self._logger.error("Could not get full URL. Wrong username or password?")
            raise WrongCredentialsError("Wrong username or password.")
        if responds.status_code == requests.codes.not_found:  # pylint: disable=no-member
            raise WrongUrlError(f"Wrong URL: {url}")
        if responds.status_code == requests.codes.service_unavailable:  # pylint: disable=no-member
            # mydevolo sends a 503, if the gateway is offline
            self._logger.error("The requested gateway seems to be offline.")
            raise GatewayOfflineError("Gateway offline.")

        return responds.json()
