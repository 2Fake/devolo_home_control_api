import requests
import json
import websocket
import time
import threading

from mydevolo_api import Mydevolo


class MprmRestApi:
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com'):
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

        element_uid_list = []
        for uid, device_name in self._element_uid_dict.items():
            for element_uid in device_name:
                if element_uid.startswith('devolo.Meter'):
                    element_uid_list.append(f'current_consumption_{element_uid}')
                elif element_uid.startswith('devolo.BinarySwitch'):
                    element_uid_list.append(f'binary_state_{element_uid}')
        self._pub = Publisher(element_uid_list)
        print(element_uid_list)
        self.register_pub()

    def get_consumption(self, uid, consumption_type='current'):
        if consumption_type not in ['current', 'total']:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        # TODO: Prepare for more meter items as one
        return self._element_uid_dict.get(uid).get(f'devolo.Meter:{uid}').get(f'{consumption_type}_consumption')

    def update_binary_switch_state(self, uid, value=None):
        element_uid = 'devolo.BinarySwitch:' + uid
        if value is None:
            r = self._extract_data_from_element_uid(element_uid)
            self._element_uid_dict[uid][element_uid]['state'] = True if r['properties']['state'] == 1 else False
        else:
            self._element_uid_dict[uid][element_uid]['binary_switch']['state'] = value
            self._pub.dispatch(f'state_{self._element_uid_dict[element_uid]}', value)

    def update_consumption(self, uid, consumption, value=None):
        if consumption not in ['current', 'total']:
            raise ValueError('Consumption value is not valid. Only "current" and "total are allowed!')
        if value is not None:
            raise ValueError('Value is not allowed here.')
        element_uid = 'devolo.Meter:' + uid
        r = self._extract_data_from_element_uid(element_uid)
        value = r['properties']['currentValue'] if consumption == 'currentValue' else r['properties']['totalValue']
        self._element_uid_dict[uid][element_uid]['current_consumption'] = value

    def get_binary_switch_state(self, uid):
        return self._element_uid_dict.get(uid).get(f'devolo.BinarySwitch:{uid}').get('state')

    def get_current_consumption(self, uid):
        try:
            return self._element_uid_dict.get(uid).get(f'devolo.Meter:{uid}').get('current_consumption')
        except AttributeError:
            # TODO 1D Relay does not have a consumption. We should do a better error handling here.
            return None

    def set_binary_switch_state(self, uid: str, state: bool):
        # TODO Change to UUID
        """
        Set the binary switch to the desired state
        :param uid: uid
        :param state: Desired state of the binary switch of the device
        :return:
        """
        self.set_binary_switch(element_uid=f'devolo.BinarySwitch:{uid}', state=state)

    def register_pub(self):
        for uid in self._element_uid_dict:
            for element_uid in self._element_uid_dict[uid]:
                if element_uid.startswith('devolo.Meter'):
                    self._element_uid_dict[uid][element_uid]['subscriber'] = Subscriber(uid)
                    self._pub.register(f'current_consumption_{element_uid}', self._element_uid_dict[uid][element_uid]['subscriber'])
                elif element_uid.startswith('devolo.BinarySwitch'):
                    self._element_uid_dict[uid][element_uid]['subscriber'] = Subscriber(uid)
                    self._pub.register(f'binary_state_{element_uid}', self._element_uid_dict[uid][element_uid]['subscriber'])

    def update_devices(self):
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
                for uid in element_uids:
                    self._element_uid_dict[device][uid] = {}
                    self._element_uid_dict[device]['name'] = name

    def get_devices(self):
        return self._devices

    def get_binary_switch_devices(self):
        devices = []
        for uid, device in self._element_uid_dict.items():
            [devices.append(device) for element_uid in self._element_uid_dict.get(uid) if element_uid.startswith('devolo.BinarySwitch')]
        return devices

    def update_groups(self):
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
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{uid}"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        for x in r.json()["result"]["items"]:
            return x['properties']['itemName'], x['properties']["elementUIDs"]

    def _extract_data_from_element_uid(self, element_uid):
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{element_uid}"], 0]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch error!
        return r.json()['result']['items'][0]

    def set_binary_switch(self, element_uid, state: bool):
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': [f"{element_uid}", "turnOn" if state else "turnOff", []]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch errors!

    def get_element_uid(self, element_uid):
        """
        Return the FIM UID of the given element uid
        :param element_uid:
        :return: FIM UID as string
        """
        return element_uid.split(":", 1)


class MprmWebSocket(MprmRestApi):
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com'):
        super().__init__(user, password, gateway_serial, mydevolo_url, mprm_url)
        self._ws = None

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
            self.update_consumption(element_uid=message.get("properties").get("uid"), consumption="current", value=message.get('properties').get('property.value.new'))
        elif message['properties']['uid'].startswith('devolo.BinarySwitch') and message['properties']['property.name'] == 'state':
            self.update_binary_switch_state(element_uid=message.get("properties").get("uid"), value=True if message.get('properties').get('property.value.new') == 1 else False)
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

    def update_consumption(self, element_uid, consumption, value=None):
        if consumption not in ['current', 'total']:
            raise ValueError('Consumption value is not valid. Only "current" and "total are allowed!')
        if value is None:
            raise ValueError('Got value==None. This is impossible')
        uid = element_uid.split(":", 1)[1].split("#")[0]
        self._element_uid_dict[uid][element_uid][f'{consumption}_consumption'] = value
        self._pub.dispatch(f'current_consumption_{element_uid}', value)


class Publisher:
    def __init__(self, events):
        # maps event names to subscribers
        # str -> dict
        self.events = {event: dict()
                       for event in events}

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


if __name__ == "__main__":

    user = "username"
    password = "password"
    mydevolo = Mydevolo(user=user, password=password, url='https://dcloud-test.devolo.net')
    uuid = mydevolo.get_uuid()
    gateways_serials = mydevolo.get_gateway_serials()
    api = MprmRestApi(user=user,
                      password=password,
                      mydevolo_url=mydevolo.get_url(),
                      mprm_url="https://mprm-test.devolo.net",
                      gateway_serial="1406126500001876")
    # print(api.get_binary_switch_devices())

    # state = api.update_binary_switch_state(device_name=device_name)
    # print(f'state: {state}')
    # api.set_binary_switch_state(device_name=device_name, state=not state)
    # sleep(2)
    # state = api.get_binary_switch_state(device_name=device_name)
    # print(f'state: {state}')

    def websocket(*args):
        mprm_websocket = MprmWebSocket(user=user,
                                       password=password,
                                       mydevolo_url=mydevolo.get_url(),
                                       mprm_url="https://mprm-test.devolo.net",
                                       gateway_serial="1406126500001876")
        mprm_websocket.web_socket_connection(cookies=api.session.cookies)

    threading.Thread(target=websocket).start()
    # while True:
    #     time.sleep(1)
    #     print(f'Binary Switch: {api.get_binary_switch_state(device_name=device_name)}')
    #     print(f'Consumption: {api.get_current_consumption(device_name=device_name)}')


