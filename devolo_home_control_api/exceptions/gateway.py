"""Exceptions occurring when talking to the devolo Home Control central unit."""


class GatewayOfflineError(Exception):
    """The requested gateway is offline and cannot be used."""

    def __init__(self) -> None:
        """Initialize error."""
        super().__init__("Gateway is offline.")
