import json
import threading
import time

import websocket
from requests import ConnectionError, ReadTimeout
from urllib3.connection import ConnectTimeoutError

from devolo_home_control_api.backend.mprm_rest import MprmRest


class MprmWebsocket(MprmRest):
    """
    The MprmWebsocket object handles calls to the mPRM via websockets. It does not cover all API calls, just those
    requested up to now. All calls are done in a user context, so you need to provide credentials of that user.

    :param gateway_id: Gateway ID
    :param url: URL of the mPRM stage (typically use default value)
    """

    def __init__(self, gateway_id: str, url: str = "https://homecontrol.mydevolo.com"):
        super().__init__(gateway_id, url)
        self._ws = None
        self._event_sequence = 0

        self.publisher = None
        self.on_update = None

    def _on_open(self):
        """ Callback function to keep the websocket open. """
        def run(*args):
            self._logger.info("Starting web socket connection")
            while self._ws.sock.connected:
                time.sleep(1)
        threading.Thread(target=run).start()

    def _on_message(self, message: str):
        """ Callback function to react on a message. """
        message = json.loads(message)

        event_sequence = message.get("properties").get("com.prosyst.mbs.services.remote.event.sequence.number")
        if event_sequence == self._event_sequence:
            self._event_sequence += 1
        else:
            self._logger.warning("We missed a websocket message.")
            self._event_sequence = event_sequence

        try:
            self.on_update(message)
        except TypeError:
            self._logger.error("on_update not set!")

    def _on_error(self, error):
        """ Callback function to react on errors. We will try reconnecting with prolonging intervals. """
        self._logger.error(error)

    def _on_close(self):
        """ Callback function to react on closing the websocket. """
        self._logger.info("Closed web socket connection.")
        i = 16
        while not self._ws.sock.connected:
            try:
                self._logger.info("Trying to reconnect to the gateway.")
                self.get_local_session() if self.local_ip else self.get_remote_session()
                self.websocket_connection()
                # TODO: Reset data id counter after reconnect
            except (json.JSONDecodeError, ConnectTimeoutError, ReadTimeout, ConnectionError, websocket.WebSocketException):
                self._logger.info(f"Sleeping for {i} seconds.")
                time.sleep(i)
                i = i * 2 if i < 2048 else 3600


    def websocket_connection(self):
        """ Set up the websocket connection """
        ws_url = self._mprm_url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join([str(name) + "=" + str(value) for name, value in self._session.cookies.items()])
        ws_url = f"{ws_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED," \
                 f"com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED" \
                 f"&filter=(|(GW_ID={self._gateway.id})(!(GW_ID=*)))"
        self._logger.debug(f"Connecting to {ws_url}")
        self._ws = websocket.WebSocketApp(ws_url,
                                          cookie=cookie,
                                          on_open=self._on_open,
                                          on_message=self._on_message,
                                          on_error=self._on_error,
                                          on_close=self._on_close)
        self._ws.run_forever(ping_interval=30, ping_timeout=5)


class Publisher:
    def __init__(self, events):
        # maps event names to subscribers
        # str -> dict
        self.events = {event: dict()
                       for event in events}

    def dispatch(self, event, message):
        for callback in self.get_subscribers(event).values():
            callback(message)

    def get_events(self):
        return self.events

    def get_subscribers(self, event):
        return self.events[event]

    def register(self, event, who, callback=None):
        if callback is None:
            callback = getattr(who, 'update')
        self.get_subscribers(event)[who] = callback

    def unregister(self, event, who):
        del self.get_subscribers(event)[who]
