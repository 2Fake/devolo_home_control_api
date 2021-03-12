import logging
from typing import Callable, Dict, KeysView, Union


class Publisher:
    """
    The Publisher send messages to attached subscribers.
    """

    def __init__(self, events: Union[list, KeysView]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._events: Dict = {event: {}
                              for event in events}

    def add_event(self, event: str):
        """ Add a new event to listen to. """
        self._events[event] = {}

    def delete_event(self, event: str):
        """ Delete a not longer needed event. """
        self._events.pop(event)

    def dispatch(self, event: str, message: tuple):
        """ Dispatch the message to the subscribers. """
        for callback in self._get_subscribers_for_specific_event(event).values():
            callback(message)

    def register(self, event: str, who: object, callback: Callable = None):
        """
        As a new subscriber for an event, add a callback function to call on new message.
        If no callback is given, it registers update().

        :raises AttributeError: The supposed callback is not callable.
        """
        if callback is None:
            callback = getattr(who, "update")
        self._get_subscribers_for_specific_event(event)[who] = callback
        self._logger.debug("Subscriber registered for event %s", event)

    def unregister(self, event: str, who: object):
        """ Remove a subscriber for a specific event. """
        del self._get_subscribers_for_specific_event(event)[who]
        self._logger.debug("Subscriber deleted for event %s", event)

    def _get_subscribers_for_specific_event(self, event: str) -> Dict:
        """ All subscribers listening to an event. """
        return self._events.get(event,
                                {})
