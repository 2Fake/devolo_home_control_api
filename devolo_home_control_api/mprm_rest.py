import json
import logging
import socket
import time

import requests
from zeroconf import DNSAddress, ServiceBrowser, ServiceStateChange, Zeroconf

from .devices.zwave import Zwave
from .mydevolo import Mydevolo
from .properties.binary_switch_property import BinarySwitchProperty
from .properties.consumption_property import ConsumptionProperty


class MprmRest:
    def __init__(self, user, password, gateway_id, mydevolo_url='https://www.mydevolo.com', mprm_url='https://homecontrol.mydevolo.com'):
        self._logger = logging.getLogger(self.__class__.__name__)

        mydevolo = Mydevolo(user=user, password=password, url=mydevolo_url)
        self._gateway = mydevolo.get_gateway(id=gateway_id)
        self._uuid = mydevolo.uuid

        local_ip = self._detect_gateway_in_lan()

        self._mprm_url = mprm_url if not local_ip else "http://" + local_ip
        self._rpc_url = self._mprm_url + '/remote/json-rpc'
        self._headers = {'content-type': 'application/json'}
        self._session = requests.Session()

        if local_ip:
            self._logger.info('Connecting to gateway locally')
            full_url = self._mprm_url + '/dhlp/port/full'
            # Get a token
            self._token_url = self._session.get(full_url, auth=(self._uuid, self._gateway.local_passkey)).json()
            self._session.get(self._token_url.get('link'))
        else:
            self._logger.info('Connecting to gateway via cloud')
            # Create a _session
            full_url = requests.get(mydevolo.url + '/v1/users/' + mydevolo.uuid + '/hc/gateways/' + self._gateway.id + '/fullURL', auth=(user, password), headers=self._headers).json()['url']
            self._session.get(full_url)

        # create the initial device dict
        self.devices = {}
        self.update_devices()

        for device in self.devices:
            if hasattr(self.devices[device], 'consumption_property'):
                for consumption_uid, consumption_property in self.devices[device].consumption_property.items():
                    self.update_consumption(uid=consumption_uid, consumption='current')
            if hasattr(self.devices[device], 'binary_switch_property'):
                for binary_switch in self.devices[device].binary_switch_property:
                    self.update_binary_switch_state(uid=binary_switch)

    def start_inclusion(self):
        self._logger.info("Starting inclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.PairDevice', 'pairDevice', ['PAT02-B']]}
        self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)

    def start_exclusion(self):
        self._logger.info("Starting exclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.RemoveDevice', 'removeDevice', []]}
        self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)

    def stop_inclusion(self):
        self._logger.info("Stopping inclusion")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['devolo.PairDevice', 'cancel', []]}
        self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)

    def set_name(self, uid, name):
        self._logger.debug(f"Setting name of {uid} to {name}")
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/invokeOperation',
                'params': ['gds.hdm:ZWave:F6BF9812/28', 'save', [{'name': name, 'zoneID': 'hz_1', 'icon': '', 'eventsEnabled': True}]]}
        self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)

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
        if value is not None:
            raise ValueError("Use function in mPRM web socket to update a binary state with a value")
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
        if consumption == 'current':
            self.devices[self._get_fim_uid_from_element_uid(uid)].consumption_property[uid].current_consumption = r['properties']['currentValue']
        elif consumption == 'total':
            self.devices[self._get_fim_uid_from_element_uid(uid)].consumption_property[uid].total_consumption = r['properties']['totalValue']

    def get_binary_switch_state(self, element_uid):
        """Return the internal saved binary switch state of a device."""
        return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).binary_switch_property[element_uid].state

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
        self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch errors!

    def get_current_consumption(self, element_uid):
        """Return the internal saved current consumption state of a device"""
        try:
            return self.devices.get(self._get_fim_uid_from_element_uid(element_uid)).consumption_property.get(element_uid).current_consumption
        except AttributeError:
            return None

    def update_devices(self):
        """Create the initial internal device dict"""
        # TODO: Add http, powermeter
        data = {'jsonrpc': '2.0',
                'id': 10,
                'method': 'FIM/getFunctionalItems',
                'params': [['devolo.DevicesPage'], 0]}
        r = self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)
        for item in r.json()['result']['items']:
            all_devices_list = item['properties']['deviceUIDs']
            for device in all_devices_list:
                name, element_uids, deviceModelUID = self._get_name_and_element_uids(uid=device)
                self.devices[device] = Zwave(name=name, fim_uid=device)
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
                        self._logger.debug(f"Found an unexpected element uid: {element_uid}")

    @property
    def binary_switch_devices(self):
        """Returns all binary switch devices."""
        return [self.devices.get(uid) for uid in self.devices if hasattr(self.devices.get(uid), "binary_switch_property")]

    def _detect_gateway_in_lan(self):
        """Detects a gateway in local network and check if it is the desired one."""
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                zeroconf.get_service_info(service_type, name)

        local_ip = None
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])
        # TODO: Optimize the sleep
        time.sleep(2)
        for mdns_name in zeroconf.cache.entries():
            if hasattr(mdns_name, 'address'):
                try:
                    ip = socket.inet_ntoa(mdns_name.address)
                    if requests.get('http://' + ip + '/dhlp/port/full', auth=(self._uuid, self._gateway.local_passkey)).status_code == requests.codes.ok:
                        self._logger.debug(f"Got successful answer from ip {ip}. Setting this as local gateway")
                        local_ip = ip
                        break
                except OSError:
                    # Got IPv6 address
                    self._logger.debug(f'Found an IPv6 address.')
        zeroconf.close()
        return local_ip

    def _get_name_and_element_uids(self, uid):
        """Returns the name and all element uids of the given UID"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{uid}"], 0]}
        r = self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)
        for x in r.json()["result"]["items"]:
            return x['properties']['itemName'], x['properties']["elementUIDs"], x['properties']['deviceModelUID']

    def _extract_data_from_element_uid(self, element_uid):
        """Returns data from an element_uid using a RPC call"""
        data = {'jsonrpc': '2.0',
                'id': 11,
                'method': 'FIM/getFunctionalItems',
                'params': [[f"{element_uid}"], 0]}
        r = self._session.post(self._rpc_url, data=json.dumps(data), headers=self._headers)
        # TODO: Catch error!
        return r.json()['result']['items'][0]

    def _get_fim_uid_from_element_uid(self, element_uid):
        """Return FIM UID from the given element UID"""
        return element_uid.split(':', 1)[1].split('#')[0]

    def _get_device_type_from_element_uid(self, element_uid):
        """Return the device type of the given element uid"""
        return element_uid.split(':')[0]
