"""The Publisher."""
from __future__ import annotations

import logging
from typing import Any, Callable, KeysView


class Publisher:
    """The Publisher send messages to attached subscribers."""

    def __init__(self, events: list[Any] | KeysView) -> None:
        """Initialize the publisher."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._events: dict[Any, Any] = {event: {} for event in events}

    def add_event(self, event: str) -> None:
        """Add a new event to listen to."""
        self._events[event] = {}

    def delete_event(self, event: str) -> None:
        """Delete a not longer needed event."""
        self._events.pop(event)

    def dispatch(self, event: str, message: tuple[Any, ...]) -> None:
        """Dispatch the message to the subscribers."""
        for callback in self._get_subscribers_for_specific_event(event).values():
            callback(message)

    def register(self, event: str, who: Any, callback: Callable | None = None) -> None:
        """
        As a new subscriber for an event, add a callback function to call on new message.
        If no callback is given, it registers update().

        :raises AttributeError: The supposed callback is not callable.
        """
        if callback is None:
            callback = who.update
        self._get_subscribers_for_specific_event(event)[who] = callback
        self._logger.debug("Subscriber registered for event %s", event)

    def unregister(self, event: str, who: Any) -> None:
        """Remove a subscriber for a specific event."""
        del self._get_subscribers_for_specific_event(event)[who]
        self._logger.debug("Subscriber deleted for event %s", event)

    def _get_subscribers_for_specific_event(self, event: str) -> dict[Any, Any]:
        """All subscribers listening to an event."""
        return self._events.get(event, {})
