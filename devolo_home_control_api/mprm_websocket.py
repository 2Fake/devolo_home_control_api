import json
import threading
import time

import websocket

from .mprm_rest import MprmRest


class MprmWebSocket(MprmRest):
    """
    The MprmWebSocket object handles calls to the mPRM via websockets. It does not cover all API calls, just those requested up to now.
    All calls are done in a user context, so you need to provide credentials of that user.
    :param user: devolo ID
    :param password: Corresponding password
    :param gateway_id: Gateway ID
    :param mydevolo_url: URL of the mydevolo stage (typically use default value)
    :param mprm_url: URL of the mPRM stage (typically use default value)
    """

    def __init__(self, user, password, gateway_id, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com'):
        super().__init__(user, password, gateway_id, mydevolo_url, mprm_url)
        self._ws = None
        self.publisher = None
        self.create_pub()
        threading.Thread(target=self.web_socket_connection).start()

    def create_pub(self):
        """
        Create a publisher for every element we support at the moment.
        Actual there are publisher for current consumption and binary state
        Current consumption publisher is create as "current_consumption_ELEMENT_UID"
        Binary state publisher is created as "binary_state_ELEMENT_UID"
        """
        publisher_list = []
        for device in self.devices:
            publisher_list.append(device)
        self.publisher = Publisher(publisher_list)

    def on_open(self):
        """
        Callback function to keep the websocket open.
        """
        def run(*args):
            self._logger.info("Starting web socket connection")
            while self._ws.sock.connected:
                time.sleep(1)
        threading.Thread(target=run).start()

    def on_message(self, message):
        """
        Callback function to react on a message.
        :param message: The message
        """
        message = json.loads(message)
        if message['properties']['uid'].startswith('devolo.Meter'):
            if message['properties']['property.name'] == 'currentValue':
                self.update_consumption(uid=message.get("properties").get("uid"), consumption="current", value=message.get('properties').get('property.value.new'))
            elif message['properties']['property.name'] == 'totalValue':
                self.update_consumption(uid=message.get("properties").get("uid"), consumption="total", value=message.get('properties').get('property.value.new'))
            else:
                self._logger.info(f'Unknown meter message received for {message.get("properties").get("uid")}.\n{message.get("properties")}')
        elif message['properties']['uid'].startswith('devolo.BinarySwitch') and message['properties']['property.name'] == 'state':
            self.update_binary_switch_state(uid=message.get("properties").get("uid"), value=True if message.get('properties').get('property.value.new') == 1 else False)
        else:
            # Unknown messages shall be ignored
            pass

    def on_error(self, error):
        """
        Callback function to react on errors.
        :param error: The error
        """
        # TODO: catch error
        self._logger.error(error)

    def on_close(self):
        """
        Callback function to react on closing the websocket.
        """
        self._logger.info("Closed web socket connection")

    def web_socket_connection(self):
        ws_url = self._mprm_url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join([str(name)+"="+str(value) for name, value in self._session.cookies.items()])
        ws_url = f"{ws_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED,com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED&filter=(|(GW_ID={self._gateway.id})(!(GW_ID=*)))"
        self._logger.debug(f"Connecting to {ws_url}")
        self._ws = websocket.WebSocketApp(ws_url,
                                          cookie=cookie,
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)
        self._ws.run_forever()

    def update_consumption(self, uid, consumption, value=None):
        if consumption not in ['current', 'total']:
            raise ValueError("Consumption value is not valid. Only \"current\" and \"total\" are allowed!")
        if value is None:
            super().update_consumption(uid=uid, consumption=consumption)
        else:
            for consumption_property_name, consumption_property_value in self.devices.get(self._get_fim_uid_from_element_uid(element_uid=uid)).consumption_property.items():
                if uid == consumption_property_name:
                    # Todo : make one liner
                    self._logger.debug(f"Updating {consumption} consumption of {uid}")
                    if consumption == 'current':
                        consumption_property_value.current_consumption = value
                    else:
                        consumption_property_value.total_consumption = value
            self.publisher.dispatch(self._get_fim_uid_from_element_uid(uid), value)

    def update_binary_switch_state(self, uid, value=None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a websocket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param value: bool
        """
        if value is None:
            super().update_binary_switch_state(uid=uid)
        else:
            for binary_switch_name, binary_switch_property_value in self.devices[self._get_fim_uid_from_element_uid(element_uid=uid)].binary_switch_property.items():
                if binary_switch_name == uid:
                    self._logger.debug(f"Updating state of {uid}")
                    binary_switch_property_value.state = value
            self.publisher.dispatch(self._get_fim_uid_from_element_uid(uid), value)


class Publisher:
    def __init__(self, events):
        # maps event names to subscribers
        # str -> dict
        self.events = {event: dict()
                       for event in events}

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

    def dispatch(self, event, message):
        for callback in self.get_subscribers(event).values():
            callback(message)
