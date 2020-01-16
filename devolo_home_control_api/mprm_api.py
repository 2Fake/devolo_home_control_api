import traceback

import requests
import json
import websocket
import time
import threading

try:
    from mydevolo_api import Mydevolo
except ModuleNotFoundError:
    from .mydevolo_api import Mydevolo


class MprmRestApi:
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com', create_publisher=True):
        mydevolo = Mydevolo(user=user, password=password, url=mydevolo_url)
        self._mprm_url = mprm_url
        self._gateway_serial = gateway_serial
        self._headers = {'content-type': 'application/json'}
        uuid = mydevolo.get_uuid()

        self.rpc_url = self._mprm_url + "/remote/json-rpc"

        # Create a session
        self.session = requests.Session()
        full_url = requests.get(mydevolo.get_url() + "/v1/users/" + uuid + "/hc/gateways/" + self._gateway_serial + "/fullURL", auth=(user, password), headers=self._headers).json()['url']
        self.session.get(full_url)

        # create a dict with UIDs --> names
        self._element_uid_dict = {}
        # create a dict with names --> UIDs
        self._devices = {}
        self._groups = {}
        self._schedules = {}
        self._scenes = {}
        self._notifications = {}
        self._rules = {}
        self.update_devices()
        self.update_groups()
        self.update_schedules()
        self.update_scenes()
        self.update_notifications()
        self.update_rules()
        for device in self._element_uid_dict:
            for uid in self._element_uid_dict.get(device).get('element_uids'):
                if uid.startswith('devolo.Meter'):
                    self.update_consumption(uid=uid, consumption='current')
                elif uid.startswith('devolo.BinarySwitch'):
                    self.update_binary_switch_state(uid=uid)

    def get_consumption(self, uid, consumption_type='current'):
        """
        Return the consumption, specified in consumption_type for the given uid.
        :param uid: UID as string
        :param consumption_type: 'current' or 'total' consumption
        :return: Consumption as float
        """
        if consumption_type not in ['current', 'total']:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        # TODO: Prepare for more meter items as one
        return self._element_uid_dict.get(uid).get(f'devolo.Meter:{uid}').get(f'{consumption_type}_consumption')

    def update_binary_switch_state(self, uid, value=None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param value: bool
        """
        if not uid.startswith('devolo.BinarySwitch:'):
            raise ValueError('Not a valid uid to get binary switch data')
        if value is None:
            r = self._extract_data_from_element_uid(uid)
            self._element_uid_dict[uid.split(":", 1)[1].split("#")[0]]['element_uids'][uid]['state'] = True if r['properties']['state'] == 1 else False
        else:
            self._element_uid_dict[uid.split(":", 1)[1].split("#")[0]]['element_uids'][uid]['binary_switch']['state'] = value
            self._pub.dispatch(f'state_{self._element_uid_dict[uid]}', value)

    def update_consumption(self, uid, consumption, value=None):
        """
        Function to update the internal consumption of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param consumption: String, which consumption is meant (current or total)
        :param value: consumption value as float
        """
        if consumption not in ['current', 'total']:
            raise ValueError('Consumption value is not valid. Only "current" and "total are allowed!')
        if value is not None:
            raise ValueError('Value is not allowed here.')
        r = self._extract_data_from_element_uid(uid)
        value = r['properties']['currentValue'] if consumption == 'currentValue' else r['properties']['totalValue']
        self._element_uid_dict[uid.split(":", 1)[1].split("#")[0]]['element_uids'][uid]['current_consumption'] = value

    def get_binary_switch_state(self, uid):
        """Return the internal saved binary switch state of a device."""
        return self._element_uid_dict.get(uid.split(":", 1)[1].split("#")[0]).get('element_uids').get(uid).get('state')

    def get_current_consumption(self, uid):
        """Return the internal saved current consumption state of a device"""
        try:
            return self._element_uid_dict.get(uid.split(":", 1)[1].split("#")[0]).get('element_uids').get(uid).get('current_consumption')
        except AttributeError:
            # TODO 1D Relay does not have a consumption. We should do a better error handling here.
            return None

    def set_binary_switch_state(self, uid: str, state: bool):
        """
        Set the binary switch to the desired state
        :param uid: uid
        :param state: Desired state of the binary switch of the device
        :return:
        """
        self.set_binary_switch(element_uid=uid, state=state)

    def update_devices(self):
        """Create the initial internal device dict"""
        # TODO: Add http, hue, powermeter
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.DevicesPage"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._devices = {}
        self._element_uid_dict = {}
        for item in r.json()['result']['items']:
            all_devices_list = item['properties']['deviceUIDs']
            for device in all_devices_list:
                name, element_uids = self._get_name_and_element_uids(uid=device)
                self._element_uid_dict[device] = {}
                self._element_uid_dict[device]['element_uids'] = {}
                for uid in element_uids:
                    self._element_uid_dict[device]['element_uids'][uid] = {}
                    self._element_uid_dict[device]['name'] = name

    def get_uids(self):
        """Returns the element_uid_dict with all information in it"""
        return self._element_uid_dict

    def get_binary_switch_devices(self):
        """Returns all binary switch devices."""
        devices = []
        for uid in self._element_uid_dict:
            [devices.append(self._element_uid_dict.get(uid)) for element_uid in self._element_uid_dict.get(uid).get('element_uids') if element_uid.startswith('devolo.BinarySwitch')]
        return devices

    def update_groups(self):
        """Create the initial internal groups dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Grouping"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._groups = {}
        for item in r.json()['result']['items']:
            all_groups_list = item['properties']['smartGroupWidgetUIDs']
            for group in all_groups_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=group)
                self._groups[name] = elementUIDs

    def update_schedules(self):
        """Create the initial internal schedules dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Schedules"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._schedules = {}
        for item in r.json()['result']['items']:
            all_schedules_list = item['properties']['scheduleUIDs']
            for schedule in all_schedules_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=schedule)
                self._schedules[name] = elementUIDs

    def update_notifications(self):
        """Create the initial internal notifications dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Messages"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._notifications = {}
        for item in r.json()['result']['items']:
            all_notifications_list = item['properties']['customMessageUIDs']
            for notification in all_notifications_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=notification)
                self._notifications[name] = elementUIDs

    def update_rules(self):
        """Create the initial internal rules dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Services"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._rules = {}
        for item in r.json()['result']['items']:
            all_rules_list = item['properties']['serviceUIDs']
            for rule in all_rules_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=rule)
                self._rules[name] = elementUIDs

    def update_scenes(self):
        """Create the initial internal scenes dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Scene"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._scenes = {}
        for item in r.json()['result']['items']:
            all_scenes_list = item['properties']['sceneUIDs']
            for scene in all_scenes_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=scene)
                self._scenes[name] = elementUIDs

    def _get_name_and_element_uids(self, uid):
        """Returns the name and all element uids of the given UID"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{uid}"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        for x in r.json()["result"]["items"]:
            return x['properties']['itemName'], x['properties']["elementUIDs"]

    def _extract_data_from_element_uid(self, element_uid):
        """Returns data from an element_uid using a RPC call"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{element_uid}"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch error!
        return r.json()['result']['items'][0]

    def set_binary_switch(self, element_uid, state: bool):
        """
        Set the binary switch of the given element_uid to the given state
        :param element_uid: element_uid as string
        :param state: Bool
        """
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': [f"{element_uid}", "turnOn" if state else "turnOff", []]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch errors!


class MprmWebSocket(MprmRestApi):
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com', create_publisher=True):
        super().__init__(user, password, gateway_serial, mydevolo_url, mprm_url, create_publisher=False)
        self._ws = None
        if create_publisher:
            self._pub = None
            self.create_pub()
        ####################################################
        # Uncomment the next line for testing
        # self.register_sub()

    def create_pub(self):
        """
        Create a publisher for every element we support at the moment.
        Actual there are publisher for current consumption and binary state
        Current consumption publisher is create as "current_consumption_ELEMENT_UID"
        Binary state publisher is created as "binary_state_ELEMENT_UID"
        """
        element_uid_list = []
        for uid in self._element_uid_dict:
            for element_uid in self._element_uid_dict.get(uid).get('element_uids'):
                if element_uid.startswith('devolo.Meter'):
                    element_uid_list.append(f'current_consumption_{element_uid}')
                elif element_uid.startswith('devolo.BinarySwitch'):
                    element_uid_list.append(f'binary_state_{element_uid}')
        self._pub = Publisher(element_uid_list)

    def register_sub(self):
        """
        Register a Subscriber for every element we support at the moment.
        This method is more or less an example how to use the publisher created in 'create_pub'
        Actual there are publisher for current consumption and binary state
        Current consumption publisher is create as "current_consumption_ELEMENT_UID"
        Binary state publisher is created as "binary_state_ELEMENT_UID"
        :return:
        """
        for uid in self._element_uid_dict:
            for element_uid in self._element_uid_dict.get(uid).get('element_uids'):
                if element_uid.startswith('devolo.Meter'):
                    self._element_uid_dict[uid]['element_uids'][element_uid]['subscriber'] = Subscriber(element_uid)
                    self._pub.register(f'current_consumption_{element_uid}', self._element_uid_dict[uid]['element_uids'][element_uid]['subscriber'])
                elif element_uid.startswith('devolo.BinarySwitch'):
                    self._element_uid_dict[uid]['element_uids'][element_uid]['subscriber'] = Subscriber(element_uid)
                    self._pub.register(f'binary_state_{element_uid}', self._element_uid_dict[uid]['element_uids'][element_uid]['subscriber'])

    def get_publisher(self):
        return self._pub

    def on_open(self):
        def run(*args):
            # TODO: replace by logger
            print('Starting web socket connection')
            while True:
                time.sleep(1)
            time.sleep(1)
            self._ws.close()
            # TODO: replace by logger
            print("thread terminating...")

        threading.Thread(target=run).start()

    def on_message(self, message):
        message = json.loads(message)
        if message['properties']['uid'].startswith('devolo.Meter'):
            # TODO: distinguish between current and total value
            self.update_consumption(uid=message.get("properties").get("uid"), consumption="current", value=message.get('properties').get('property.value.new'))
        elif message['properties']['uid'].startswith('devolo.BinarySwitch') and message['properties']['property.name'] == 'state':
            self.update_binary_switch_state(uid=message.get("properties").get("uid"), value=True if message.get('properties').get('property.value.new') == 1 else False)
        else:
            # Unknown messages shall be ignored
            pass

    def on_error(self, error):
        # TODO: replace by logger
        print(error)

    def on_close(self):
        # TODO: replace by logger
        print("### closed ###")

    def web_socket_connection(self, cookies: dict):
        import websocket  # TODO: Find out why we nee the import here. Otherwise it throws an error --> AttributeError: 'function' object has no attribute 'WebSocketApp'
        ws_url = self._mprm_url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join([str(name)+"="+str(value) for name, value in cookies.items()])
        ws_url = f"{ws_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED,com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED&filter=(|(GW_ID={self._gateway_serial})(!(GW_ID=*)))"
        self._ws = websocket.WebSocketApp(ws_url,
                                          cookie=cookie,
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)
        self._ws.run_forever()

    def update_consumption(self, uid, consumption, value=None):
        if consumption not in ['current', 'total']:
            raise ValueError('Consumption value is not valid. Only "current" and "total are allowed!')
        if value is None:
            super().update_consumption(uid=uid, consumption='current')
            return
            # raise ValueError('Got value==None. This is impossible')
        self._element_uid_dict[uid.split(":", 1)[1].split("#")[0]]['element_uids'][uid][f'{consumption}_consumption'] = value
        self._pub.dispatch(f'current_consumption_{uid}', value)

    def update_binary_switch_state(self, uid, value=None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param value: bool
        """
        if value is None:
            super().update_binary_switch_state(uid=uid)
            return
        self._element_uid_dict[uid.split(":", 1)[1].split("#")[0]]['element_uids'][uid]['state'] = value
        self._pub.dispatch(f"binary_state_{uid}", value)


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
        if callback == None:
            callback = getattr(who, 'update')
        self.get_subscribers(event)[who] = callback

    def unregister(self, event, who):
        del self.get_subscribers(event)[who]

    def dispatch(self, event, message):
        for subscriber, callback in self.get_subscribers(event).items():
            callback(message)


class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        print('{} got message "{}"'.format(self.name, message))
