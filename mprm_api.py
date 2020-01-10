import requests
import json
import websocket
import time
import _thread as thread    # TODO: replace by threading

from mydevolo_api import Mydevolo


class MprmWebSocket:
    def __init__(self, mprm_rest_api):
        self._mprm_rest_api = mprm_rest_api
        self._ws = None

    def on_open(self):
        def run(*args):
            # TODO: replace by logger
            print('Starting websocket connection')
            while True:
                time.sleep(1)
            time.sleep(1)
            self._ws.close()
            # TODO: replace by logger
            print("thread terminating...")

        thread.start_new_thread(run, ())

    def on_message(self, message):
        message = json.loads(message)
        if message['properties']['uid'].startswith('devolo.Meter'):
            self._mprm_rest_api.update_consumption(element_uid=message.get("properties").get("uid"), value=message.get('properties').get('property.value.new'))
        elif message['properties']['uid'].startswith('devolo.BinarySwitch') and message['properties']['property.name'] == 'state':
            # TODO: replace by logger
            print(f'We got a new binary switch value for device {message.get("properties").get("uid")}')
            self._mprm_rest_api.update_binary_switch_state(element_uid=message.get("properties").get("uid"), value=True if message.get('properties').get('data') == 1 else False)
        else:
            pass

    def on_error(self, error):
        # TODO: replace by logger
        print(error)

    def on_close(self):
        # TODO: replace by logger
        print("### closed ###")

    def web_socket_connection(self, cookies: dict):
        mprm_url = self._mprm_rest_api.get_mprm_url()
        cookie = "; ".join([str(name)+"="+str(value) for name, value in cookies.items()])
        gateway_serial = self._mprm_rest_api.get_gateway_serial()
        ws_url = f"ws://{mprm_url}/remote/events/?topics=com/prosyst/mbs/services/fim/FunctionalItemEvent/PROPERTY_CHANGED,com/prosyst/mbs/services/fim/FunctionalItemEvent/UNREGISTERED&filter=(|(GW_ID={gateway_serial})(!(GW_ID=*)))"
        self._ws = websocket.WebSocketApp(ws_url,
                                          cookie=cookie,
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)
        self._ws.run_forever()


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

    def update_binary_switch_state(self, element_uid=None, device_name=None, value=None):
        if element_uid is None and device_name is None:
            raise ValueError('Got not information about a device or an elementUID')
        if value is None:
            # TODO: Catch error
            if device_name and not element_uid:
                try:
                    r = self._extract_data_from_element_uid(self._devices.get(device_name).get('binary_switch').get('uid'))
                    self._devices[device_name]['binary_switch']['state'] = True if r['properties']['state'] == 1 else False
                    return True
                except KeyError:
                    raise KeyError(f"The device {device_name} does not have a binary switch")
            elif element_uid and not device_name:
                r = self._extract_data_from_element_uid(element_uid)
                self._devices[self._element_uid_dict[element_uid]]['binary_switch']['state'] = True if r['properties']['state'] == 1 else False
                return True
            elif element_uid and device_name:
                r = self._extract_data_from_element_uid(element_uid)
                self._devices[device_name]['binary_switch']['state'] = True if r['properties']['state'] == 1 else False
                return True
            return False
        else:
            self._devices[self._element_uid_dict[element_uid]]['binary_switch']['state'] = value

    def update_consumption(self, element_uid=None, device_name=None, value=None):
        if element_uid is None and device_name is None:
            raise ValueError('Got not information about a device or an elementUID')
        if not value:
            self._devices[self._element_uid_dict[element_uid]]['current_consumption']['consumption'] = None
            # TODO:
        else:
            self._devices[self._element_uid_dict[element_uid]]['current_consumption']['consumption'] = value

    def get_binary_switch_state(self, device_name):
        return self._devices.get(device_name).get('binary_switch').get('state')

    def get_current_consumption(self, device_name):
        return self._devices.get(device_name).get('current_consumption').get('consumption')

    def set_binary_switch_state(self, device_name: str, state: bool):
        """
        Set the binary switch to the desired state
        :param device_name: Name of the device
        :param state: Desired state of the binary switch of the device
        :return:
        """
        self.set_binary_switch(element_uid=self._devices.get(device_name).get('binary_switch').get('uid'), state=state)
        self.update_binary_switch_state(element_uid=self._devices.get(device_name).get('binary_switch').get('uid'), device_name=device_name)

    def get_specific_element_uid(self, device_name: str, element_uid: str) -> list:
        """
        Get a specific element uid of a device
        :param device_name: Name of the device
        :param element_uid: Start of string
        :return: List of element UID with probably one element
        """
        return [s for s in self._devices.get(device_name) if element_uid in s]

    def get_gateway_serial(self) -> str:
        return self._gateway_serial

    def get_mprm_url(self) -> str:
        return self._mprm_url

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
                name, elementUIDs = self._get_name_and_elementUIDs(uid=device)
                self._devices[name] = {}
                self._devices[name]['element_uids'] = elementUIDs
                for i in elementUIDs:
                    self._element_uid_dict[i] = name
                    if i.startswith('devolo.BinarySwitch'):
                        self._devices[name]['binary_switch'] = {}
                        self._devices[name]['binary_switch']['uid'] = i
                        self.update_binary_switch_state(element_uid=i)
                    elif i.startswith('devolo.Meter'):
                        self._devices[name]['current_consumption'] = {}
                        self._devices[name]['current_consumption']['uid'] = i
                        self.update_consumption(element_uid=i)

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
        return r.json()['result']['items'][0]

    def set_binary_switch(self, element_uid, state: bool):
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': [f"{element_uid}", "turnOn" if state else "turnOff", []]}
        r = self.session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch errors!
        print(json.dumps(r.json(), indent=4))


if __name__ == "__main__":
    # usage example:

    from time import sleep

    user = "username"
    password = "password"
    mydevolo = Mydevolo(user=user, password=password, url='https://dcloud-test.devolo.net')
    # uuid = mydevolo.get_uuid()
    # gateways_serials = mydevolo.get_gateway_serials()
    # localPasskey = mydevolo.get_local_passkey(serial="1406126500001876")
    #
    api = MprmRestApi(user=user,
                      password=password,
                      mydevolo_url=mydevolo.get_url(),
                      mprm_url="https://mprm-test.devolo.net",
                      gateway_serial="1406126500001876")
    # print(api.get_binary_switch_devices())
    device_name = 'Relay'
    # state = api.update_binary_switch_state(device_name=device_name)
    # print(f'state: {state}')
    # api.set_binary_switch_state(device_name=device_name, state=not state)
    # sleep(2)
    # state = api.get_binary_switch_state(device_name=device_name)
    # print(f'state: {state}')
    def websocket(*args):
        mprm_websocket = MprmWebSocket(mprm_rest_api=api)
        mprm_websocket.web_socket_connection(cookies=api.session.cookies)

    thread.start_new_thread(websocket, ())
    while True:
        time.sleep(1)
        print(f'Binary Switch: {api.get_binary_switch_state(device_name=device_name)}')
        print(f'Consumption: {api.get_current_consumption(device_name=device_name)}')
