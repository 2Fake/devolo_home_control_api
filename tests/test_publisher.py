"""Test the publisher."""
from devolo_home_control_api.publisher import Publisher

from . import Subscriber


def test_adding() -> None:
    """Test adding an event."""
    publisher = Publisher(events=[])
    publisher.add_event("test_event")
    subscriber = Subscriber("test_subscriber")
    publisher.register("test_event", subscriber)
    publisher.dispatch("test_event", ())
    subscriber.update.assert_called_once()


def test_deleting() -> None:
    """Test deleting an event."""
    publisher = Publisher(events=["test_event"])
    subscriber = Subscriber("test_subscriber")
    publisher.register("test_event", subscriber)
    publisher.delete_event("test_event")
    publisher.dispatch("test_event", ())
    subscriber.update.assert_not_called()


def test_unregister() -> None:
    """Test unregistering from the publisher."""
    publisher = Publisher(events=["test_event"])
    subscriber = Subscriber("test_subscriber")
    publisher.register("test_event", subscriber)
    publisher.unregister("test_event", subscriber)
    publisher.dispatch("test_event", ())
    subscriber.update.assert_not_called()
