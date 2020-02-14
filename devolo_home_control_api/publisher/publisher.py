class Publisher:
    """
    The Publisher send messages to attached subscribers.
    """

    def __init__(self, events: list):
        self._events = {event: dict() for event in events}


    def dispatch(self, event: str, message: str):
        """ Dispatch the message to the subscribers. """
        for callback in self._subscribers(event).values():
            callback(message)

    def register(self, event: str, who: object, callback: callable = None):
        """
        As a new subscriber for an event, add a callback function to call on new message.
        If no callback is given, it registers update().

        :raises AttributeError: The supposed callback is not callable.
        """
        if callback is None:
            callback = getattr(who, 'update')
        self._subscribers(event)[who] = callback

    def unregister(self, event: str, who: object):
        """ Remove a subscriber for a specific event. """
        del self._subscribers(event)[who]
 

    def _subscribers(self, event: str):
        """ All subscribers listening to an event. """
        return self._events[event]
