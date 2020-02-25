import json
import threading
import time

import websocket
from requests import ConnectionError, ReadTimeout
from urllib3.connection import ConnectTimeoutError

from devolo_home_control_api.backend.mprm_rest import MprmRest, MprmDeviceCommunicationError


class MprmWebsocket(MprmRest):
    """
    The MprmWebsocket object handles calls to the mPRM via websockets. It does not cover all API calls, just those
    requested up to now. All calls are done in a gateway context, so you need to provide the ID of that gateway. As
    it inherites from MprmRest, it is a singleton as well.

    :param gateway_id: Gateway ID (aka serial number), typically found on the label of the device
    :param url: URL of the mPRM
    """

    def __init__(self, gateway_id: str, url: str):
        super().__init__(gateway_id, url)
        self._ws = None
        self._event_sequence = 0

        self.publisher = None
        self.on_update = None


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


    def _on_close(self):
        """ Callback function to react on closing the websocket. """
        self._logger.info("Closed web socket connection.")

    def _on_error(self, error: str):
        """ Callback function to react on errors. We will try reconnecting with prolonging intervals. """
        self._logger.error(error)
        self.connected = False
        self._ws.close()
        self._event_sequence = 0

        sleep_interval = 16
        while not self.connected:
            self._try_reconnect(sleep_interval)
            sleep_interval = sleep_interval * 2 if sleep_interval < 2048 else 3600

        self.websocket_connection()

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
            self._logger.error("on_update is not set.")

    def _on_open(self):
        """ Callback function to keep the websocket open. """
        def run(*args):
            self._logger.info("Starting web socket connection")
            while self._ws.sock is not None and self._ws.sock.connected:
                time.sleep(1)
        threading.Thread(target=run).start()

    def _try_reconnect(self, sleep_interval: int):
        try:
            self._logger.info("Trying to reconnect to the gateway.")
            # TODO: Check if local_ip is still correct after lost connection
            self.get_local_session() if self._local_ip else self.get_remote_session()
            self.connected = True
        except (json.JSONDecodeError, ConnectTimeoutError, ReadTimeout, ConnectionError, MprmDeviceCommunicationError):
            self._logger.info(f"Sleeping for {sleep_interval} seconds.")
            time.sleep(sleep_interval)
