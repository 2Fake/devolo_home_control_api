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

        devices_list = []
        for uid, device_name in self._element_uid_dict.items():
            if uid.startswith('devolo.Meter'):
                devices_list.append(f'current_consumption_{uid}')
            elif uid.startswith('devolo.BinarySwitch'):
                devices_list.append(f'state_{uid}')
        print(devices_list)
        self._pub = Publisher(devices_list)
        self.register_pub()

    def get_consumption_of_every_device(self, consumption_type='current'):
        device_consumption_dict = {}
        for device in self._devices.keys():
            try:
                device_consumption_dict[device] = self.get_consumption(device_name=device, consumption_type=consumption_type)
            except IndexError:
                # The device does not have a consumption
                pass
        return device_consumption_dict

    def get_consumption(self, device_name, consumption_type='current'):
        # As only devices can have a consumption, we don't need to search for it in other dicts than devices.
        if consumption_type not in ['current', 'total']:
            raise ValueError('Unknown consumption type. "current" and "total" are valid consumption types.')
        if device_name not in self._devices:
            raise ValueError(f"Device '{device_name}' not found. Did you provide the correct name?")
        elementUID = [s for s in self._devices.get(device_name) if 'devolo.Meter' in s]
        try:
            r = self._extract_data_from_element_uid(elementUID[0])
        except IndexError:
            raise IndexError(f"The device {device_name} does not have a consumption")
        return float(r['properties']['currentValue'] if consumption_type == 'current' else r['properties']['totalValue'])

    def get_binary_switch_state_of_all_devices(self):
        device_binary_switch_state_dict = {}
        for device in self._devices.keys():
            try:
                device_binary_switch_state_dict[device] = self.get_binary_switch_state(device_name=device)
            except IndexError:
                # The device does not have a binary switch
                pass
        return device_binary_switch_state_dict

    def update_binary_switch_state(self, element_uid, value=None):
        if value is None:
            r = self._extract_data_from_element_uid(element_uid)
            self._element_uid_dict[element_uid]['state'] = True if r['properties']['state'] == 1 else False
        else:
            self._element_uid_dict[element_uid]['binary_switch']['state'] = value
            self._pub.dispatch(f'state_{self._element_uid_dict[element_uid]}', value)

    def update_consumption(self, element_uid, consumption, value=None):
        if consumption not in ['current_consumption', 'total_consumption']:
            raise ValueError('Consumption value is not valid. Only "current_consumption" and "total_consumption are allowed!')
        if value is None:
            r = self._extract_data_from_element_uid(element_uid)
            value = r['properties']['currentValue']
            self._element_uid_dict[element_uid]['current_consumption'] = value
        else:
            self._element_uid_dict[element_uid][consumption] = value
            self._pub.dispatch(f'current_consumption_{element_uid}', value)

    def get_binary_switch_state(self, device_name):
        return self._devices.get(device_name).get('binary_switch').get('state')

    def get_current_consumption(self, device_name):
        try:
            return self._devices.get(device_name).get('current_consumption').get('consumption')
        except AttributeError:
            # TODO 1D Relay does not have a consumption. We should do a better error handling here.
            return None

    def set_binary_switch_state(self, device_name: str, state: bool):
        """
        Set the binary switch to the desired state
        :param device_name: Name of the device
        :param state: Desired state of the binary switch of the device
        :return:
        """
        self.set_binary_switch(element_uid=self._devices.get(device_name).get('binary_switch').get('uid'), state=state)
        # self.update_binary_switch_state(element_uid=self._devices.get(device_name).get('binary_switch').get('uid'), device_name=device_name)

    def get_specific_element_uid(self, device_name: str, element_uid: str) -> list:
        """
        Get a specific element uid of a device
        :param device_name: Name of the device
        :param element_uid: Start of string
        :return: List of element UID with probably one element
        """
        return [s for s in self._devices.get(device_name) if element_uid in s]

    def register_pub(self):
        for uid in self._element_uid_dict:
            if uid.startswith('devolo.Meter'):
                self._element_uid_dict[uid]['subscriber'] = Subscriber(uid)
                self._pub.register(f'current_consumption_{uid}', self._element_uid_dict[uid]['subscriber'])
            elif uid.startswith('devolo.BinarySwitch'):
                self._element_uid_dict[uid]['subscriber'] = Subscriber(uid)
                self._pub.register(f'state_{uid}', self._element_uid_dict[uid]['subscriber'])

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
                name, element_uids = self._get_name_and_elementUIDs(uid=device)
                # self._devices[name] = {}
                # self._devices[name]['element_uids'] = element_uids
                for uid in element_uids:
                    self._element_uid_dict[uid] = {}
                    self._element_uid_dict[uid]['name'] = name
                    if uid.startswith('devolo.BinarySwitch'):
                        self._element_uid_dict[uid]['state'] = self.update_binary_switch_state(element_uid=uid)
                    elif uid.startswith('devolo.Meter'):
                        self._element_uid_dict[uid]['current_consumption'] = self.update_consumption(element_uid=uid)

    def get_devices(self):
        return self._devices

    def get_binary_switch_devices(self):
        devices = []
        for uid, device in self._element_uid_dict.items():
            if uid.startswith('devolo.BinarySwitch'):
                devices.append(device)
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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=group)
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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=schedule)
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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=notification)
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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=rule)
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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=scene)
                self._scenes[name] = elementUIDs

    def _get_name_and_elementUIDs(self, uid):
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
            print(message)
            self.update_consumption(element_uid=message.get("properties").get("uid"), value=message.get('properties').get('property.value.new'))
        elif message['properties']['uid'].startswith('devolo.BinarySwitch') and message['properties']['property.name'] == 'state':
            self.update_binary_switch_state(element_uid=message.get("properties").get("uid"), value=True if message.get('properties').get('property.value.new') == 1 else False)
        else:
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
    # usage example:

    from time import sleep

    user = "username"
    password = "password"
    mydevolo = Mydevolo(user=user, password=password, url='https://dcloud-test.devolo.net')
    uuid = mydevolo.get_uuid()
    gateways_serials = mydevolo.get_gateway_serials()
    # localPasskey = mydevolo.get_local_passkey(serial="1406126500001876")
    #
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


