"""Mock methods from the zeroconf package."""
from __future__ import annotations

from typing import Any, Callable
from unittest.mock import Mock

from zeroconf import ServiceStateChange, Zeroconf


class MockServiceBrowser:
    """Mock of the ServiceBrowser."""

    cancel = Mock()

    def __init__(self, zeroconf: Zeroconf, type_: str, handlers: list[Callable], **__: Any) -> None:
        """Initialize the service browser."""
        handlers[0](zeroconf, type_, type_, ServiceStateChange.Added)
