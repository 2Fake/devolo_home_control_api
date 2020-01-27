import json
import threading
import time

import websocket

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
        if consumption_type not in ["current", "total"]:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        if consumption_type == "current":
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.current
        else:
            return self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.total

    def update_binary_switch_state(self, element_uid: str, value: bool = None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like, devolo.BinarySwitch:hdm:ZWave:CBC56091/24#2
        :param value: Value so be set
        """
        if value is None:
            super().get_binary_switch_state(element_uid=element_uid)
        else:
            for binary_switch_name, binary_switch_property_value in self.devices.get(get_device_uid_from_element_uid(element_uid)).binary_switch_property.items():
                if binary_switch_name == element_uid:
                    self._logger.debug(f"Updating state of {element_uid}")
                    binary_switch_property_value.state = value
            self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), value)

    def update_consumption(self, element_uid: str, consumption: str, value: float = None):
        """
        Function to update the internal consumption of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like , something like devolo.MultiLevelSensor:hdm:ZWave:CBC56091/24#2
        :param consumption: current or total consumption
        :param value: Value so be set
        """
        if consumption not in ["current", "total"]:
            raise ValueError('Consumption value is not valid. Only "current" and "total" are allowed!')
        if value is None:
            super().get_consumption(element_uid=element_uid, consumption_type=consumption)
        else:
            for consumption_property_name, consumption_property_value in self.devices.get(get_device_uid_from_element_uid(element_uid)).consumption_property.items():
                if element_uid == consumption_property_name:
                    self._logger.debug(f"Updating {consumption} consumption of {element_uid}")
                    # TODO : make one liner
                    if consumption == "current":
                        consumption_property_value.current = value
                    else:
                        consumption_property_value.total = value
            self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), value)

    def update_voltage(self, element_uid: str, value: float = None):
        """
        Function to update the internal voltage of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.

        :param element_uid: Element UID, something like devolo.VoltageMultiLevelSensor:hdm:ZWave:CBC56091/24
        :param value: Value so be set
        """
        if value is None:
            super().get_voltage(element_uid=element_uid)
        else:
            for voltage_property_name, voltage_property_value in self.devices.get(get_device_uid_from_element_uid(element_uid)).voltage_property.items():
                if element_uid == voltage_property_name:
                    self._logger.debug(f"Updating voltage of {element_uid}")
                    voltage_property_value.current = value
            self.publisher.dispatch(get_device_uid_from_element_uid(element_uid), value)


    def _create_pub(self):
        """
        Create a publisher for every element we support at the moment.
        Actual there are publisher for current consumption and binary state
        Current consumption publisher is create as "current_consumption_ELEMENT_UID"
        Binary state publisher is created as "binary_state_ELEMENT_UID"
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
        else:
            # Unknown messages shall be ignored
            pass

    def _on_error(self, error):
        """ Callback function to react on errors. """
        # TODO: catch error
        self._logger.error(error)

    def _on_close(self):
        """ Callback function to react on closing the websocket. """
        self._logger.info("Closed web socket connection")

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
        self._ws.run_forever(ping_interval=30)


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
