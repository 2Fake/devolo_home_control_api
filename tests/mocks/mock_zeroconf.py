"""Mock methods from the zeroconf package."""
from typing import Any, Callable, List
from unittest.mock import Mock

from zeroconf import ServiceStateChange, Zeroconf


class MockServiceBrowser:
    """Mock of the ServiceBrowser."""

    cancel = Mock()

    def __init__(self, zeroconf: Zeroconf, type_: str, handlers: List[Callable], **__: Any) -> None:
        """Initialize the service browser."""
        handlers[0](zeroconf, type_, type_, ServiceStateChange.Added)
