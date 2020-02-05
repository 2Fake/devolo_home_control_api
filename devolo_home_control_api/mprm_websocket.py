import json
import threading
import time

import websocket
from requests import ConnectionError, ReadTimeout
from urllib3.connection import ConnectTimeoutError

from .mprm_rest import MprmRest, get_device_uid_from_element_uid


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

        self._create_pub()
        threading.Thread(target=self._websocket_connection).start()


    def get_consumption(self, element_uid: str, consumption_type: str = "current") -> float:
        """
        Return the internal saved consumption, specified in consumption_type for the given uid.

        :param element_uid: element UID of the consumption. Usually starts with devolo.Meter
        :param consumption_type: current or total consumption
        :return: Consumption
        """
        if not element_uid.startswith("devolo.Meter"):
            raise ValueError("Not a valid uid to get consumption data.")
        if consumption_type not in ["current", "total"]:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        if consumption_type == "current":
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current
        else:
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).total

    def update_binary_switch_state(self, element_uid: str, value: bool = None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: Value so be set
        """
        if not element_uid.startswith("devolo.BinarySwitch"):
            raise ValueError("Not a valid uid to set binary switch state.")
        if value is None:
            self.get_binary_switch_state(element_uid=element_uid)
        else:
            for binary_switch_name, binary_switch_property_value in \
                    self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.items():
                if binary_switch_name == element_uid:
                    self._logger.debug(f"Updating state of {element_uid}")
                    binary_switch_property_value.state = value
            message = (element_uid, value)
            self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), message)

    def update_consumption(self, element_uid: str, consumption: str, value: float = None):
        """
        Function to update the internal consumption of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like , something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param consumption: current or total consumption
        :param value: Value so be set
        """
        if not element_uid.startswith("devolo.Meter"):
            raise ValueError("Not a valid uid to set consumption data.")
        if consumption not in ["current", "total"]:
            raise ValueError(f'Consumption value "{consumption}" is not valid. Only "current" and "total" are allowed.')
        if value is None:
            super().get_consumption(element_uid=element_uid, consumption_type=consumption)
        else:
            for consumption_property_name, consumption_property_value in \
                    self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.items():
                if element_uid == consumption_property_name:
                    self._logger.debug(f"Updating {consumption} consumption of {element_uid} to {value}")
                    # TODO : make one liner
                    if consumption == "current":
                        consumption_property_value.current = value
                    else:
                        consumption_property_value.total = value
        message = (element_uid, value)
        self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), message)

    def update_gateway_state(self, accessible: bool, online_sync: bool):
        """
        Function to update the gateway status. A gateway might go on- or offline while we listen to the websocket.

        :param accessible: Online state of the gateway
        :param online_sync: Sync state of the gateway
        """
        self._logger.debug(f"Updating status and state of gateway to status: {accessible} and state: {online_sync}")
        self._gateway.online = accessible
        self._gateway.sync = online_sync

    def update_voltage(self, element_uid: str, value: float = None):
        """
        Function to update the internal voltage of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
        :param value: Value so be set
        """
        if not element_uid.startswith("devolo.VoltageMultiLevelSensor"):
            raise ValueError("Not a valid uid to set voltage data.")
        if value is None:
            self.get_voltage(element_uid=element_uid)
        else:
            for voltage_property_name, voltage_property_value in \
                    self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.items():
                if element_uid == voltage_property_name:
                    self._logger.debug(f"Updating voltage of {element_uid}")
                    voltage_property_value.current = value
            message = (element_uid, value)
            self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), message)


    def _create_pub(self):
        """
        Create a publisher for every element we support at the moment.
        Actually, there are publisher for current consumption and binary state. Current consumption publisher is create as
        "current_consumption_ELEMENT_UID" and binary state publisher is created as "binary_state_ELEMENT_UID".
        """
        publisher_list = [device for device in self.devices]
        self.publisher = Publisher(publisher_list)

    def _on_open(self):
        """ Callback function to keep the websocket open. """
        def run(*args):
            self._logger.info("Starting web socket connection")
            while self._ws.sock.connected:
                time.sleep(1)
        threading.Thread(target=run).start()

    def _on_message(self, message):
        """ Callback function to react on a message. """
        message = json.loads(message)
        event_sequence = message.get("properties").get("com.prosyst.mbs.services.remote.event.sequence.number")
        if event_sequence == self._event_sequence:
            self._event_sequence += 1
        else:
            self._logger.warning("We missed a websocket message.")
            self._event_sequence = event_sequence
        if message.get("properties").get("uid").startswith("devolo.Meter"):
            if message.get("properties").get("property.name") == "currentValue":
                self.update_consumption(element_uid=message.get("properties").get("uid"),
                                        consumption="current",
                                        value=message.get("properties").get("property.value.new"))
            elif message.get("properties").get("property.name") == "totalValue":
                self.update_consumption(element_uid=message.get("properties").get("uid"),
                                        consumption="total", value=message.get("properties").get("property.value.new"))
            else:
                self._logger.info(f'Unknown meter message received for {message.get("properties").get("uid")}.')
                self._logger.info(message.get("properties"))
        elif message.get("properties").get("uid").startswith("devolo.BinarySwitch") \
                and message.get("properties").get("property.name") == "state":
            self.update_binary_switch_state(element_uid=message.get("properties").get("uid"),
                                            value=True if message.get("properties").get("property.value.new") == 1
                                            else False)
        elif message.get("properties").get("uid").startswith("devolo.VoltageMultiLevelSensor"):
            self.update_voltage(element_uid=message.get("properties").get("uid"),
                                value=message.get("properties").get("property.value.new"))
        elif message.get("properties").get("uid") == "devolo.mprm.gw.GatewayAccessibilityFI" \
                and message.get("properties").get("property.name") == "gatewayAccessible":
            self.update_gateway_state(accessible=message.get("properties").get("property.value.new").get("accessible"),
                                      online_sync=message.get("properties").get("property.value.new").get("onlineSync"))

        else:
            # Unknown messages shall be ignored
            self._logger.debug(json.dumps(message, indent=4))

    def _on_error(self, error):
        """ Callback function to react on errors. We will try reconnecting with prolonging intervals. """
        self._logger.error(error)


    def _on_close(self):
        """ Callback function to react on closing the websocket. """
        self._logger.info("Closed web socket connection")
        i = 16
        while not self._ws.sock.connected:
            try:
                self._logger.info("Trying to reconnect to the gateway.")
                if self.local_ip:
                    self._get_local_session()
                else:
                    self._get_remote_session()
                self._websocket_connection()
            except (json.JSONDecodeError, ConnectTimeoutError, ReadTimeout, ConnectionError, websocket.WebSocketException):
                self._logger.info(f"Sleeping for {i} seconds.")
                time.sleep(i)
                if i < 3600:
                    i *= 2
                else:
                    i = 3600

    def _websocket_connection(self):
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
