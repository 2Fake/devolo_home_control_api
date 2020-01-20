import json
import logging
import threading
import time
import socket
import requests
import websocket
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf, DNSAddress

from .property_classes.binary_switch_property import BinarySwitchProperty
from .property_classes.consumption_property import ConsumptionProperty
from .device_classes.device import Device
from .mydevolo_api import Mydevolo


class MprmRestApi:
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com', create_publisher=True):
        mydevolo = Mydevolo(user=user, password=password, url=mydevolo_url)
        # TODO: Check if the correct gateway was found locally

        local_ip = self._detect_gateway_in_lan()
        local_ip = False

        self._mprm_url = mprm_url if not local_ip else "http://" + local_ip
        self._gateway_serial = gateway_serial
        self._headers = {'content-type': 'application/json'}

        self._session = requests.Session()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.rpc_url = self._mprm_url + '/remote/json-rpc'

        if local_ip:
            self._logger.info('Connecting to gateway locally')
            self._local_passkey = mydevolo.get_local_passkey(serial=gateway_serial)
            full_url = self._mprm_url + '/dhlp/port/full'
            # Get a token
            self._token_url = self._session.get(full_url, auth=(mydevolo.uuid, self._local_passkey)).json()
            self._session.get(self._token_url.get('link'))
        else:
            # Create a _session
            full_url = requests.get(mydevolo.url + '/v1/users/' + mydevolo.uuid + '/hc/gateways/' + self._gateway_serial + '/fullURL', auth=(user, password), headers=self._headers).json()['url']
            self._session.get(full_url)

        # create a dict with UIDs --> names
        self._element_uid_dict = {}
        # create a dict with names --> UIDs
        self.devices = {}
        self.groups = {}
        self.schedules = {}
        self.scenes = {}
        self.notifications = {}
        self.rules = {}
        self.update_devices()
        # self.update_groups()
        # self.update_schedules()
        # self.update_scenes()
        # self.update_notifications()
        # self.update_rules()
        for device in self.devices:
            if hasattr(self.devices[device], 'consumption_property'):
                for consumption_uid, consumption_property in self.devices[device].consumption_property.items():
                    self.update_consumption(uid=consumption_uid, consumption='current')
            if hasattr(self.devices[device], 'binary_switch_property'):
                for binary_switch in self.devices[device].binary_switch_property:
                    self.update_binary_switch_state(uid=binary_switch)
        print()

    def start_inclusion(self):
        self._logger.info("Starting inclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.PairDevice', 'pairDevice', ['PAT02-B']]}
        self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)

    def start_exclusion(self):
        self._logger.info("Starting exclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.RemoveDevice', 'removeDevice', []]}
        self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)

    def stop_inclusion(self):
        self._logger.info("Stopping inclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.PairDevice', 'cancel', []]}
        self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)

    def set_name(self, uid, name):
        self._logger.debug(f"Setting name of {uid} to {name}")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['gds.hdm:ZWave:F6BF9812/28', 'save', [{'name': name, 'zoneID': 'hz_1', 'icon': '', 'eventsEnabled': True}]]}
        self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)

    def get_consumption(self, uid, consumption_type='current'):
        """
        Return the consumption, specified in consumption_type for the given uid.
        :param uid: UID as string
        :param consumption_type: 'current' or 'total' consumption
        :return: Consumption as float
        """
        if consumption_type not in ['current', 'total']:
            raise ValueError("Unknown consumption type. \"current\" and \"total\" are valid consumption types.")
        # TODO: Prepare for more meter items as one
        return self._element_uid_dict.get(uid).get(f"devolo.Meter:{uid}").get(f"{consumption_type}_consumption")

    def update_binary_switch_state(self, uid, value=None):
        """
        Function to update the internal binary switch state of a device.
        If value is None, it uses a RPC-Call to retrieve the value. If a value is given, e.g. from a web socket,
        the value is written into the internal dict.
        :param uid: UID as string
        :param value: bool
        """
        if not uid.startswith('devolo.BinarySwitch:'):
            raise ValueError("Not a valid uid to get binary switch data")
        if value != None:
            raise ValueError("Use function in mPRM Websocket to update a binary state with a value")
        self._logger.debug(f"Updating state of {uid}")
        r = self._extract_data_from_element_uid(uid)
        self.devices[self._get_fim_uid_from_element_uid(uid)].binary_switch_property[uid].state = True if r['properties']['state'] == 1 else False

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
            raise ValueError("Consumption value is not valid. Only \"current\" and \"total\" are allowed!")
        if value is not None:
            raise ValueError("Value is not allowed here.")
        self._logger.debug(f"Updating {consumption} consumption of {uid}")
        r = self._extract_data_from_element_uid(uid)
        value = r['properties']['currentValue'] if consumption == 'currentValue' else r['properties']['totalValue']
        # TODO: correct current and total value
        self.devices[self._get_fim_uid_from_element_uid(uid)].consumption_property[uid].current_consumption = value

    def get_binary_switch_state(self, element_uid):
        """Return the internal saved binary switch state of a device."""
        return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).binary_switch_property[element_uid].state

    def get_current_consumption(self, element_uid):
        """Return the internal saved current consumption state of a device"""
        try:
            return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current_consumption
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
        # TODO: check, if this method is useless
        self.set_binary_switch(element_uid=uid, state=state)

    def update_devices(self):
        """Create the initial internal device dict"""
        # TODO: Add http, powermeter
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [['devolo.DevicesPage'], 0]}
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self.devices = {}
        for item in r.json()['result']['items']:
            all_devices_list = item['properties']['deviceUIDs']
            for device in all_devices_list:
                name, element_uids, deviceModelUID = self._get_name_and_element_uids(uid=device)
                # TODO: Rethink this!
                self.devices[device] = Device(name=name, fim_uid=device)
                for element_uid in element_uids:
                    if self._get_device_type_from_element_uid(element_uid) == 'devolo.BinarySwitch':
                        if not hasattr(self.devices[device], 'binary_switch_property'):
                            self.devices[device].binary_switch_property = {}
                        self._logger.debug(f"Adding {name} ({device}) to device list as binary switch property.")
                        self.devices[device].binary_switch_property[element_uid] = BinarySwitchProperty(element_uid=element_uid)
                    elif self._get_device_type_from_element_uid(element_uid) == 'devolo.Meter':
                        if not hasattr(self.devices[device], 'consumption_property'):
                            self.devices[device].consumption_property = {}
                            self._logger.debug(f"Adding {name} ({device}) to device list as consumption property.")
                            self.devices[device].consumption_property[element_uid] = ConsumptionProperty(element_uid=element_uid)
                    # TODO:
                    else:
                        self._logger.info(f"Found an unexpected element uid: {element_uid}")

    def get_binary_switch_devices(self):
        """Returns all binary switch devices."""
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_switch_property")]

    def update_groups(self):
        """Create the initial internal groups dict"""
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [["devolo.Grouping"], 0]}
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
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
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
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
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
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
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
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
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        self._scenes = {}
        for item in r.json()['result']['items']:
            all_scenes_list = item['properties']['sceneUIDs']
            for scene in all_scenes_list:
                name, elementUIDs = self._get_name_and_element_uids(uid=scene)
                self._scenes[name] = elementUIDs

    def _detect_gateway_in_lan(self):
        # TODO: Prepare for gateways in LAN which are not the needed one
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                zeroconf.get_service_info(service_type, name)

        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])
        time.sleep(2)
        try:
            local_ip = socket.inet_ntoa(zeroconf.cache.entries_with_name('devolo-homecontrol-2.local.')[1].address)
            # TODO: prepare for more than one gateway in LAN
        except IndexError:
            local_ip = False
        zeroconf.close()
        return local_ip

    def _get_name_and_element_uids(self, uid):
        """Returns the name and all element uids of the given UID"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{uid}"], 0]}
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        for x in r.json()["result"]["items"]:
            return x['properties']['itemName'], x['properties']["elementUIDs"], x['properties']['deviceModelUID']

    def _extract_data_from_element_uid(self, element_uid):
        """Returns data from an element_uid using a RPC call"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{element_uid}"], 0]}
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch error!
        return r.json()['result']['items'][0]

    def set_binary_switch(self, element_uid, state: bool):
        """
        Set the binary switch of the given element_uid to the given state
        :param element_uid: element_uid as string
        :param state: Bool
        """
        # TODO: We should think about how to prevent an jumping binary switch in the UI of hass
        # Maybe set the state of the binary internally without waiting for the websocket to tell us the state.
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': [f"{element_uid}", 'turnOn' if state else 'turnOff', []]}
        r = self._session.post(self.rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch errors!

    def _get_fim_uid_from_element_uid(self, element_uid):
        return element_uid.split(':', 1)[1].split('#')[0]

    def _get_device_type_from_element_uid(self, element_uid):
        return element_uid.split(':')[0]

class MprmWebSocket(MprmRestApi):
    def __init__(self, user, password, gateway_serial, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com'):
        super().__init__(user, password, gateway_serial, mydevolo_url, mprm_url)
        self._ws = None
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
        publisher_list = []
        for device in self.devices:
            publisher_list.append(device)
        self._pub = Publisher(publisher_list)

    def register_sub(self):
        """
        Register a Subscriber for every element we support at the moment.
        This method is more or less an example how to use the publisher created in 'create_pub'
        A publisher exists for every device
        Current consumption publisher is create as "FIM_UD"
        :return:
        """
        for device in self.devices:
            self.devices[device].subscriber = Subscriber(device)
            self._pub.register(device, self.devices[device].subscriber)

    def get_publisher(self):
        return self._pub

    def on_open(self):
        def run(*args):
            self._logger.info("Starting web socket connection")
            while True:
                time.sleep(1)
            time.sleep(1)
            self._ws.close()
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
        # TODO: catch error
        self._logger.error(error)

    def on_close(self):
        # TODO: We need to think about a way to restart the web socket connection if it is closed.
        self._logger.info("Closed web socket connection")

    def web_socket_connection(self):
        import websocket  # TODO: Find out why we nee the import here. Otherwise it throws an error --> AttributeError: 'function' object has no attribute 'WebSocketApp'
        ws_url = self._mprm_url.replace("https://", "wss://").replace("http://", "ws://")
        cookie = "; ".join([str(name)+"="+str(value) for name, value in self._session.cookies.items()])
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
            self._pub.dispatch(self._get_fim_uid_from_element_uid(uid), value)

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
        else:
            for binary_switch_name, binary_switch_property_value in self.devices[self._get_fim_uid_from_element_uid(element_uid=uid)].binary_switch_property.items():
                if binary_switch_name == uid:
                    self._logger.debug(f"Updating state of {uid}")
                    binary_switch_property_value.state = value
            self._pub.dispatch(self._get_fim_uid_from_element_uid(uid), value)


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
        for subscriber, callback in self.get_subscribers(event).items():
            callback(message)


class Subscriber:
    def __init__(self, name):
        self.name = name

    def update(self, message):
        print('{} got message "{}"'.format(self.name, message))
