"""Expections used in this package."""
from .device import SwitchingProtected, WrongElementError
from .gateway import GatewayOfflineError
from .general import WrongCredentialsError, WrongUrlError

__all__ = ["GatewayOfflineError", "SwitchingProtected", "WrongCredentialsError", "WrongElementError", "WrongUrlError"]
