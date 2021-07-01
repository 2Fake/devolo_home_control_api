import json
import threading
import time
from abc import ABC, abstractmethod

import requests
import websocket
from pkg_resources import parse_version
from urllib3.connection import ConnectTimeoutError

from ..exceptions.gateway import GatewayOfflineError
from .mprm_rest import MprmRest


class MprmWebsocket(MprmRest, ABC):
    """
    The abstract MprmWebsocket object handles calls to the mPRM via websockets. It does not cover all API calls, just those
    requested up to now. All calls are done in a gateway context, so you have to create a derived class, that provides a
    Gateway object and a Session object. Further, the derived class needs to implement methods to connect to the websocket,
    either local or remote. Last but not least, the derived class needs to implement a method that is called on new messages.

    The websocket connection itself runs in a thread, that might not terminate as expected. Using a with-statement is
    recommended.
    """

    def __init__(self):
        super().__init__()
        self._ws: websocket.WebSocketApp = None
        self._connected = False  # This attribute saves, if the websocket is fully established
        self._reachable = True  # This attribute saves, if the a new session can be established
        self._event_sequence = 0

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.websocket_disconnect()

    @abstractmethod
    def detect_gateway_in_lan(self):
        pass

    @abstractmethod
    def get_local_session(self):
        pass

    @abstractmethod
    def get_remote_session(self):
        pass

    @abstractmethod
    def on_update(self, message):
        pass

    def wait_for_websocket_establishment(self):
        """
        In some cases it is needed to wait for the websocket to be fully established. This method can be used to block your
        current thread for up to one minute.
        """
        start_time = time.time()
        while not self._connected and time.time() < start_time + 600:
            time.sleep(0.1)
        if not self._connected:
            self._logger.debug("Websocket could not be established")
            raise GatewayOfflineError("Websocket could not be established.")

    def websocket_connect(self):
        """
        Set up the websocket connection. The protocol type of the known session URL is exchanged depending on whether TLS is
        used or not. After establishing the websocket, a ping is sent every 30 seconds to keep the connection alive. If there
        is no response within 5 seconds, the connection is terminated with error state.
        """
        ws_url = self._url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join(str(name) + "=" + str(value) for name, value in self._session.cookies.items())

        ws_url = f"{ws_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED," \
                 f"com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED" \
                 f"&filter=(|(GW_ID={self.gateway.id})(!(GW_ID=*)))"
        self._logger.debug("Connecting to %s", ws_url)
        if parse_version(websocket.__version__) < parse_version("0.58.0"):  # Just in case we hit an outdated version
            self._logger.warning(
                "Please consider updating your websocket-client version. Support for <0.58.0 will be removed soon.")
            self._ws = websocket.WebSocketApp(ws_url,
                                              cookie=cookie,
                                              on_open=self._on_open_old,
                                              on_message=self._on_message_old,
                                              on_error=self._on_error_old,
                                              on_close=self._on_close_old,
                                              on_pong=self._on_pong_old)
        else:
            self._ws = websocket.WebSocketApp(ws_url,
                                              cookie=cookie,
                                              on_open=self._on_open,
                                              on_message=self._on_message,
                                              on_error=self._on_error,
                                              on_close=self._on_close,
                                              on_pong=self._on_pong)
        self._ws.run_forever(ping_interval=30, ping_timeout=5)

    def websocket_disconnect(self, event: str = ""):
        """
        Close the websocket connection.
        """
        self._logger.info("Closing web socket connection.")
        if event:
            self._logger.info("Reason: %s", event)
        self._ws.close()

    def _on_close(self, ws: websocket.WebSocketApp):  # pylint: disable=unused-argument
        """ Callback method to react on closing the websocket. """
        self._logger.info("Closed websocket connection.")

    def _on_close_old(self):
        """ Deprecated callback method to react on closing the websocket. """
        self._on_close(ws=self._ws)

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception):
        """ Callback method to react on errors. We will try reconnecting with prolonging intervals. """
        self._logger.exception(error)
        self._connected = False
        self._reachable = False
        ws.close()
        self._event_sequence = 0

        sleep_interval = 16
        while not self._reachable:
            self._try_reconnect(sleep_interval)
            sleep_interval = sleep_interval * 2 if sleep_interval < 2048 else 3600

        self.websocket_connect()

    def _on_error_old(self, error: Exception):
        """ Deprecated callback method to react on errors. """
        self._on_error(ws=self._ws, error=error)

    def _on_message(self, ws: websocket.WebSocketApp, message: str):  # pylint: disable=unused-argument
        """ Callback method to react on a message. """
        msg = json.loads(message)
        self._logger.debug("Got message from websocket:\n%s", msg)
        event_sequence = msg["properties"]["com.prosyst.mbs.services.remote.event.sequence.number"]
        if event_sequence == self._event_sequence:
            self._event_sequence += 1
        else:
            self._logger.warning(
                "We missed a websocket message. Internal event_sequence is at %s. "
                "Event sequence by websocket is at %s",
                self._event_sequence,
                event_sequence)
            self._event_sequence = event_sequence + 1
            self._logger.debug("self._event_sequence is set to %s", self._event_sequence)

        self.on_update(msg)

    def _on_message_old(self, message: str):
        """ Deprecated callback method to react on a message. """
        self._on_message(ws=self._ws, message=message)

    def _on_open(self, ws: websocket.WebSocketApp):
        """ Callback method to keep the websocket open. """

        def run():
            self._logger.info("Starting web socket connection.")
            while ws.sock is not None and ws.sock.connected:
                time.sleep(1)

        threading.Thread(target=run, name=f"{self.__class__.__name__}.websocket_run").start()
        self._connected = True

    def _on_open_old(self):
        """ Deprecated callback method to keep the websocket open. """
        self._on_open(ws=self._ws)

    def _on_pong(self, ws: websocket.WebSocketApp, *args):  # pylint: disable=unused-argument
        """ Callback method to keep the session valid. """
        self.refresh_session()

    def _on_pong_old(self, *args):
        """ Deprecated callback method to keep the session valid. """
        self._on_pong(ws=self._ws, *args)

    def _try_reconnect(self, sleep_interval: int):
        """ Try to reconnect to the websocket. """
        try:
            self._logger.info("Trying to reconnect to the websocket.")
            self._reachable = self.get_local_session() if self._local_ip else self.get_remote_session()
        except (ConnectTimeoutError, GatewayOfflineError):
            self._logger.info("Sleeping for %s seconds.", sleep_interval)
            time.sleep(sleep_interval)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            self._logger.info("Sleeping for %s seconds.", sleep_interval)
            time.sleep(sleep_interval - 3)  # mDNS browsing will take up tp 3 seconds by itself
            self.detect_gateway_in_lan()
