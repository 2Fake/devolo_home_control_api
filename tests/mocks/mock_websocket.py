"""Mock methods from the websocket package."""
from __future__ import annotations

from typing import Any, Callable

from websocket import ABNF, WebSocket, WebSocketApp
from websocket._url import parse_url


class Dispatcher:
    """Custom dispatcher that makes the read callback available to the outside."""

    def __init__(self) -> None:
        """Initialize the dispatcher."""
        self.read_callback: Callable[[], None]

    def read(self, _: Any, read_callback: Callable[[], None]) -> None:
        """Store the callback on read activity."""
        self.read_callback = read_callback

    def signal(self, *args: Any) -> None:
        """Mock signaling."""

    def abort(self, *args: Any) -> None:
        """Mock aborting."""


class SockMock:
    """Mock receiving data via websocket."""

    def __init__(self) -> None:
        """Initialize the mock."""
        self.data: list[bytes] = []

    def add_packet(self, data: str) -> None:
        """Add data to the socket's stack."""
        frame = ABNF.create_frame(data.encode("UTF-8"), ABNF.OPCODE_TEXT)
        self.data.append(frame.format())
        DISPATCHER.read_callback()

    def close(self) -> None:
        """Mock closing the socket."""

    def gettimeout(self) -> None:
        """Mock a timeout value."""

    def recv(self, bufsize: int) -> bytes:
        """Mock receiving data."""
        if self.data:
            datum = self.data.pop(0)
            if isinstance(datum, Exception):
                raise datum
            if len(datum) > bufsize:
                self.data.insert(0, datum[bufsize:])
            return datum[:bufsize]
        return b""


class WebSocketMock(WebSocket):
    """Mock the websocket interface."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the websocket."""
        super().__init__(**kwargs)
        self.connected = True
        self.sock = SockMock()
        self.recv_packet = self.sock.add_packet

    def close(self, *_: Any, **__: Any) -> None:
        """Mock closing the socket."""
        self.sock.add_packet(str(ABNF.OPCODE_CLOSE))

    def error(self) -> None:
        """Mock an error during an open connection."""
        self.sock.add_packet("")

    def recv_pong(self) -> None:
        """Mock receiving a pong message."""
        self.sock.add_packet(str(ABNF.OPCODE_PONG))


class MockWebSocketApp(WebSocketApp):
    """Mock of the websocket app."""

    sock: WebSocketMock

    def run_forever(self, *_: Any, **__: Any) -> None:
        """Create a forever running websocket connection."""

        def check() -> bool:
            """Mock checking the websocket connectivity."""
            return True

        def read() -> None:
            """Call registered callback method."""
            data = self.sock.recv()
            if not data:
                self._callback(self.on_error, self, Exception)
            elif data == str(ABNF.OPCODE_PONG):
                self._callback(self.on_pong, data)
            elif data == str(ABNF.OPCODE_CLOSE):
                self._callback(self.on_close, data, "")
            else:
                self._callback(self.on_message, data)

        self.keep_running = True
        self.sock = WEBSOCKET
        self._callback(self.on_open)
        dispatcher = self.create_dispatcher(None, DISPATCHER, parse_url(self.url)[3])
        dispatcher.read(self.sock.sock, read, check)


DISPATCHER = Dispatcher()
WEBSOCKET = WebSocketMock()
