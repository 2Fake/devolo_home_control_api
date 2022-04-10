"""Exceptions occuring when talking to the devolo Home Control central unit."""


class GatewayOfflineError(Exception):
    """The requested gateway is offline and cannot be used."""
